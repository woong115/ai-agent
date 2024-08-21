from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.globals import set_debug
from langchain.memory import ConversationBufferWindowMemory
from langchain.retrievers.parent_document_retriever import ParentDocumentRetriever
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.stores import BaseStore
from langchain_core.vectorstores.base import VectorStore

from app.application.port.chat_engine import ChatEngine
from app.infrastructure.langchain.async_redis_chat_message_history import (
    AsyncRedisChatMessageHistory,
)
from app.infrastructure.langchain.few_shot import answer_examples
from app.infrastructure.langchain.text_splitters import (
    child_text_splitter,
    parent_text_splitter,
)


def inspect(state):
    """Print the state passed between Runnables in a langchain and pass it on"""
    print(state)
    return state


class ChatEngineLangchainImpl(ChatEngine):
    def __init__(
        self,
        llm: BaseChatModel,
        docstore: BaseStore,
        vectorstore: VectorStore,
        history_db_url: str,
        max_history_k: int,
    ):
        self.llm = llm
        # self.retriever = vectorstore.as_retriever(
        #     search_kwargs={"k": 5},
        #     # search_kwargs={"k": 4},
        #     # search_kwargs = {"k": 8},
        #     # search_type="mmr",
        #     # search_kwargs={"k": 4, "fetch_k": 8},
        #     # search_type="mmr",
        #     # search_kwargs={"k": 3, "fetch_k": 6},
        # )
        self.retriever = ParentDocumentRetriever(
            vectorstore=vectorstore,
            docstore=docstore,
            child_splitter=child_text_splitter,
            parent_splitter=parent_text_splitter,
        )
        self.history_db_url = history_db_url
        self.max_history_k = max_history_k
        self.rag_chain = self._get_rag_chain()

    def _get_session_history(self, session_id: str) -> AsyncRedisChatMessageHistory:
        return AsyncRedisChatMessageHistory(
            url=self.history_db_url,
            session_id=session_id,
            ttl=3600,
            k=self.max_history_k,
        )

    def _get_history_retriever(self):
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        history_aware_retriever = create_history_aware_retriever(
            self.llm,
            self.retriever,
            contextualize_q_prompt,
        )
        return history_aware_retriever

    def _get_rag_chain(self):
        llm = self.llm
        example_prompt = ChatPromptTemplate.from_messages(
            [
                ("human", "{input}"),
                ("ai", "{answer}"),
            ]
        )
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            examples=answer_examples,
        )

        system_prompt = (
            "당신은 금융분야 마이데이터 신용정보법 가이드라인 및 API 규격 대해서 알려주는 에이전트입니다."
            "아래에 제공된 문서를 활용해서 답변해주시고"
            "제공된 문서가 없거나 답변을 알 수 없다면 모른다고 답변해주세요."
            "없는 말은 지어내지 말아주세요."
            "제공된 문서에 ![](app/static/data/금융분야 마이데이터 기술 가이드라인/images/금융분야 마이데이터 기술 가이드라인.pdf-xx-x.png) 와 같은 사진이 존재할 경우,"
            "답변에 포함해서 같이 전달해주세요."
            "\n\n"
            "{context}"
        )

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                few_shot_prompt,
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        history_aware_retriever = self._get_history_retriever()
        # history_aware_retriever = history_aware_retriever | RunnableLambda(inspect)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            self._get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        ).pick("answer")

        return conversational_rag_chain

    async def generate_chat_stream(self, session_id: str, user_message: str):
        response = await self.retriever.ainvoke(user_message)
        print(f"count of relevant documents: {len(response)}", flush=True)
        for r in response:
            print(r, flush=True)

        chat_stream = self.rag_chain.astream(
            {"input": user_message},
            config={"configurable": {"session_id": session_id}},
        )

        return chat_stream

    async def find_chat_histories(self, session_id: str):
        chat_history = self._get_session_history(session_id)
        return await chat_history.aget_messages()

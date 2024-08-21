import argparse
import os
import shutil
import time
from pathlib import Path

import requests
from langchain.retrievers.parent_document_retriever import ParentDocumentRetriever
from langchain.storage import LocalFileStore
from langchain.storage._lc_store import create_kv_docstore
from langchain_chroma import Chroma
from langchain_core.documents.base import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.helper.regex import search_markdown_image_tag
from app.helper.summary_image import summary_image
from app.settings import settings


def load_vector(md_dir_path: Path, dir_name: str, docstore, vectorstore):
    print(f"Load vector for {dir_name}")

    md_path = md_dir_path / dir_name / "output.md"
    pdf_name = dir_name + ".pdf"

    # 정재 작업 - images 디렉토리에 없는 이미지tag 제거
    image_list = [str(image) for image in (md_dir_path / dir_name / "images").iterdir()]
    md_text = ""
    with open(md_path, "r", encoding="utf-8") as file:
        for line in file:
            image_tag, image_path = search_markdown_image_tag(line)
            if image_tag and image_path not in image_list:
                line = line.replace(image_tag, "")
            md_text += line

    # splitter
    parent_text_splitter = MarkdownTextSplitter(
        # chunk_size=1400,
        # chunk_overlap=200,
        chunk_size=800,
        chunk_overlap=100,
    )
    child_text_splitter = MarkdownTextSplitter(
        chunk_size=200,
        # chunk_overlap=50,
    )

    # ParentDocumentRetriever 작은 청크 조회해서 큰 청크 가져올 수 있도록
    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        child_splitter=child_text_splitter,
        parent_splitter=parent_text_splitter,
    )
    retriever.add_documents([Document(page_content=md_text, metadata={"source": pdf_name})])

    # vectorstore의 유사도 검색을 수행합니다.
    segmented_documents = retriever.vectorstore.similarity_search_with_relevance_scores(
        "고객요청에 의한 정기적 전송 예시를 알려주세요.",
    )
    for doc in segmented_documents:
        print(doc)
    relevant_docs = retriever.invoke("고객요청에 의한 정기적 전송 예시를 알려주세요.")
    for doc in relevant_docs:
        print(f"뽑은 샘플 문서 길이: {len(doc.page_content)}")
        print("=====================================")


def delete_pinecone_index():
    headers = {"Api-Key": settings.pinecone_api_key, "X-Pinecone-API-Version": "2024-07"}
    r = requests.delete(f"https://api.pinecone.io/indexes/{settings.pinecone_index_name}", headers=headers)
    if r.status_code == 404:
        return
    r.raise_for_status()


def create_pinecone_index():
    url = "https://api.pinecone.io/indexes"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Api-Key": settings.pinecone_api_key,
        "X-Pinecone-API-Version": "2024-07",
    }

    payload = {
        "name": settings.pinecone_index_name,
        "dimension": 3072,
        "metric": "cosine",
        "spec": {"serverless": {"cloud": "aws", "region": "us-east-1"}},
        "deletion_protection": "disabled",
    }
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()


def main(vectorstore_type):
    md_dir_path = Path(settings.preprocessed_markdown_dir)

    embeddings = OpenAIEmbeddings(model=settings.openai_embedding_model)

    if vectorstore_type == "chroma":
        persist_directory = settings.chroma_persist_directory
        shutil.rmtree(persist_directory, ignore_errors=True)
        # docstore 생성
        fs = LocalFileStore(persist_directory)
        docstore = create_kv_docstore(fs)
        # vectorstore 생성
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name=settings.chroma_collection_name,
        )
    if vectorstore_type == "pinecone":
        persist_directory = settings.pinecone_persist_directory
        shutil.rmtree(persist_directory, ignore_errors=True)

        # 인덱스 삭제 & 생성
        delete_pinecone_index()
        create_pinecone_index()

        # docstore 생성
        # NOTE: 추후에 remote db로 docstore를 구성해야함
        fs = LocalFileStore(persist_directory)
        docstore = create_kv_docstore(fs)
        # vectorstore 생성
        vectorstore = PineconeVectorStore(
            pinecone_api_key=settings.pinecone_api_key,
            embedding=embeddings,
            index_name=settings.pinecone_index_name,
        )

    start = time.time()

    folders = [f.name for f in os.scandir(md_dir_path) if f.is_dir()]
    for dir_name in folders:
        load_vector(md_dir_path, dir_name, docstore, vectorstore)

    print(f"Total time: {time.time() - start}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("type", type=str, default="chroma")

    args = parser.parse_args()
    vectorstore_type = args.type
    if vectorstore_type not in ["chroma", "pinecone"]:
        raise ValueError("Invalid vectorstore type")
    main(vectorstore_type)

from langchain_text_splitters import MarkdownTextSplitter

parent_text_splitter = MarkdownTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
)
child_text_splitter = MarkdownTextSplitter(
    chunk_size=200,
    # chunk_overlap=50,
)

import os
import pathlib
import time

from app.settings import settings


def pdf_to_markdown(file_path, output_markdown_path, output_image_path):
    import pymupdf4llm

    print(f"Convert to markdown {file_path}...... it will take a few minutes")
    md_text = pymupdf4llm.to_markdown(
        file_path,
        write_images=True,
        image_path=output_image_path,
    )
    pathlib.Path(output_markdown_path).write_bytes(md_text.encode())
    print(f"{file_path} -> {output_markdown_path} DONE!")


def main():
    """
    Non-multiprocessing Total time: 178.99689745903015
    multiprocessing Total time: 167.692378282547
    """
    from concurrent.futures import ProcessPoolExecutor

    pdf_dir_path = pathlib.Path(settings.pdf_dir)
    md_dir_path = pathlib.Path(settings.preprocessed_markdown_dir)

    start = time.time()

    with ProcessPoolExecutor(2) as executor:
        futures = []

        for file in os.listdir(pdf_dir_path):
            if file.endswith(".pdf"):
                file_path = pdf_dir_path / file
                filename = file.split(".")[0]
                output_dir = md_dir_path / filename
                output_image_path = output_dir / "images"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_markdown_path = output_dir / "output.md"
                # pdf_to_markdown(file_path, output_markdown_path, output_image_path)
                futures.append(executor.submit(pdf_to_markdown, file_path, output_markdown_path, output_image_path))

        for future in futures:
            future.result()

    print(f"Total time: {time.time() - start}")


if __name__ == "__main__":
    main()

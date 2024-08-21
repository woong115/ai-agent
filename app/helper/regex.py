import re

markdown_image_tag_pattern = r"!\[\]\((.*?)\)"


def search_markdown_image_tag(text):
    """
    :return: (image_tag, image_path)
    """
    searched = re.search(markdown_image_tag_pattern, text)

    if not searched:
        return False, False

    return searched.group(), searched.group(1)

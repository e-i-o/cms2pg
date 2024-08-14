import os


def resolve_if_no_extension(original_name):
    # noinspection SpellCheckingInspection
    # I didn't decide what the file extensions are called
    extensions_to_try = [".pdf", ".png", ".jpg", ".mps",
                         ".jpeg", ".jbig2", ".jb2",
                         ".PDF", ".PNG", ".JPG",
                         ".JPEG", ".JBIG2", "JB2"]

    name, ext = os.path.splitext(original_name)
    if len(ext) != 0:
        return original_name

    for ext in extensions_to_try:
        potential_path = "statement/%s%s" % (name, ext)
        if os.path.exists(potential_path):
            return name + ext

    return None


def get_converted_image_name(original_name):
    if not should_convert(original_name):
        return original_name

    name, ext = os.path.splitext(original_name)
    return "converted_" + name + ".png"


def should_convert(original_name):
    name, ext = os.path.splitext(original_name)
    if ext.lower() == ".pdf":
        return True
    if ext.lower() == ".svg":
        return True
    return False


def convert(source, target):
    os.system("convert %s %s" % (source, target))

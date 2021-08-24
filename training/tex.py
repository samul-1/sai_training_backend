import base64
import os
import re
import subprocess


def svg2img(html: str) -> str:
    """Converts inline svg elements to images.

    This is done as a work around for #75 of WeasyPrint
    https://github.com/Kozea/WeasyPrint/issues/75
    """

    SVG_ELEM_RE = re.compile(r"<svg.*?</svg>", flags=re.MULTILINE | re.DOTALL)
    B64IMG_TMPL = '<img class="inline" src="data:image/svg+xml;base64,{img_text}"/>'
    SVG_XMLNS = (
        'xmlns="http://www.w3.org/2000/svg" '
        + 'xmlns:xlink="http://www.w3.org/1999/xlink" '
    )

    while True:
        match = SVG_ELEM_RE.search(html)
        if match:
            svg_text = match.group(0)
            if "xmlns" not in svg_text:
                svg_text = svg_text.replace("<svg ", "<svg " + SVG_XMLNS)
            svg_data = svg_text.encode("utf-8")
            img_b64_data: bytes = base64.standard_b64encode(svg_data)
            img_b64_text = img_b64_data.decode("utf-8")
            img_b64_tag = B64IMG_TMPL.format(img_text=img_b64_text)
            start, end = match.span()
            html = html[:start] + img_b64_tag + html[end:]
        else:
            break

    return html


# takes in a text that might contain TeX formulas wrapped between $ or $$ tags,
# returns the original text unchanged if no $ tags are found, otherwise returns the original text
# where all the TeX formulas have been converted to svg and substituted with the svg code
def tex_to_svg(formula):
    if formula is None:
        return ""

    output_str = ""

    # tokenize the string splitting when you encounter $ tags
    tokens = [t for t in re.split(r"(\$\$?[^\$]*\$\$?)", formula)]

    for token in tokens:
        # if this token starts with $, it's a TeX formula: pass it to node and convert to svg
        if len(token) and token[0] == "$":
            if token[1] == "$":  # double $ tag = centered formula
                # strip off the $$ tags
                stripped_token = token[2:-2]
                output_str += "<p class='text-center'>"
            else:
                # strip off the $ tags
                stripped_token = token[1:-1]

            # prepend a backslash: this prevents issues if the TeX formula starts with a - character
            # which node would otherwise interpret as an argument (the node script will remove this backslash)
            stripped_token = "\\" + stripped_token

            res = subprocess.check_output(
                [
                    "node",
                    "-r",
                    "esm",
                    os.environ.get(
                        "NODE_TEX2SVG_URL", "training/tex-render/component/tex2svg"
                    ),
                    stripped_token,
                ],
            )
            # strip off the "b'" and "\n'"
            output_str += svg2img(str(res)[2:-3])
            if token[1] == "$":  # close <p> tag
                output_str += "</p>"
        else:
            output_str += token
    return output_str

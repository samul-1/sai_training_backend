import base64
import os
import re
import subprocess


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
            # also convert the html entities for &, <, etc. to their LaTeX equivalents
            stripped_token = "\\" + stripped_token.replace("&amp;", "& ").replace(
                "&gt;", "\\gt "
            ).replace("&lt;", "\\lt ").replace("&lte;", "\\le ").replace(
                "&gte;", "\\ge "
            )

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
            rendered_token = str(res)[2:-3]
            svg_occurrence = rendered_token.find("<svg") + 4
            rendered_token = (
                rendered_token[:svg_occurrence]
                + ' class="inline"'
                + rendered_token[svg_occurrence:]
            )
            output_str += rendered_token
            if token[1] == "$":  # close <p> tag
                output_str += "</p>"
        else:
            output_str += token
    return output_str

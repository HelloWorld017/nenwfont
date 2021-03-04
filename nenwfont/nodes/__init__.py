from .add_gasp import AddGaspNode
from .add_program_info import AddProgramInfoNode
from .cff_to_glyf import CFFToGlyfNode
from .input import InputNode
from .merge import MergeNode
from .output import OutputNode
from .parse_attribute import ParseAttributeNode
from .replace_attribute import ReplaceAttributeNode
from .set_attribute import SetAttributeNode
from .set_font_name import SetFontNameNode
from .subset import SubsetNode

nodes = [
    AddGaspNode,
    AddProgramInfoNode,
    CFFToGlyfNode,
    InputNode,
    MergeNode,
    OutputNode,
    ParseAttributeNode,
    ReplaceAttributeNode,
    SetAttributeNode,
    SetFontNameNode,
    SubsetNode
]

nodes_map = {
    node.name: node for node in nodes
}

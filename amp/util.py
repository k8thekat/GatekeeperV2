"""
AMP API util functions to parse API calls for specific Data.
"""
from amp.API import AMP_API
from pathlib import Path


async def getNodespec(amp: AMP_API) -> list[str]:
    """
    Creates a `setting_nodes.txt` in the script directory with nodes from api `Core/GetSettingSpec`

    Args:
        amp (AMP_API): AMP_API class object signed in.

    See -> `amp/util/setting_nodes.txt` 

    """
    res = await amp.getSettingsSpec()
    dir = Path(__file__).parent.joinpath("setting_nodes.md")
    mode = "x"
    if dir.exists():
        mode = "w"
    file = open(dir, mode)

    if not isinstance(res, dict):
        return res

    for key in res:
        for value in res[key]:
            for entry in value:
                if entry.lower() == "node":
                    file.write(f"{value[entry]} \n")


async def getPermissionNodes(amp: AMP_API) -> None:
    """
    Creates a `permission_nodes.txt` in the script directory with nodes from api `Core/GetPermissionsSpec`

    Args:
        amp (AMP_API): AMP_API class object signed in.

    See -> `amp/util/permission_nodes.txt`  
    """
    res = await amp.getPermissionsSpec()
    node_scrape(text=res)


def node_scrape(text: list[dict], file=None) -> None:
    """
    Pulls the key "Nodes" from the list of dictionary results and dumps them to a txt file.

    Args:
        text (list): The list of dictionary's
        file (_type_, optional): The file object to dump text to. Defaults to None. `**LEAVE NONE**`
    """
    dir = Path(__file__).parent.joinpath("permission_nodes.md")
    mode = "x"
    if dir.exists():
        mode = "w"

    if file == None:
        file = open(dir, mode)

    if not isinstance(text, list):
        return

    for index in text:
        if "Node" in index:
            file.write(f'{index["Node"]} \n')
        if "Children" in index:
            node_scrape(text=index["Children"], file=file)

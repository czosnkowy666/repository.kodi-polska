import os
import requests
import hashlib
import xml.etree.ElementTree as ET
import zipfile
import shutil

ADDONS = [
    "czosnkowy666/plugin.video.kodi-polska-tvp/",
    "czosnkowy666/webinterface.kodi-polska.music-player/"
]

RAW_URL = 'https://raw.githubusercontent.com/'
API_URL = 'https://api.github.com/repos/' # czosnkowy666/plugin.video.kodi-polska-tvp/releases
ZIP_DIR = "zips"
TARGET_DIR = "target"
ADDONS_TEMPLATE_PATH = "addons-template.xml"
ADDONS_XML_PATH = "addons.xml"
ADDONS_MD5_PATH = "addons.xml.md5"

def getAddonVersion(addon_path="addon.xml"):
    tree = ET.parse(addon_path)
    return tree.getroot().attrib.get("version", "0.0.1")


def getAddonId(addon_path="addon.xml"):
    tree = ET.parse(addon_path)
    return tree.getroot().attrib["id"]


def cleanBuild():
    print(f"Cleaning build: {TARGET_DIR}")
    shutil.rmtree(TARGET_DIR, ignore_errors=True)
    os.makedirs(TARGET_DIR, exist_ok=True)


def createBundle(addon_id, version):
    bundle_name = f"{addon_id}-{version}"
    bundle_zip = f"{bundle_name}.zip"
    bundle_path = os.path.join(TARGET_DIR, bundle_zip)

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in ["addon.xml", "icon.png", "fanart.jpg"]:
            if os.path.exists(file):
                zipf.write(file, arcname=os.path.join(addon_id, file))

    print(f"Created bundle: {bundle_path}")


def getAddonReleses(addonPath):
    url = API_URL + addonPath + 'releases/latest'
    response = requests.get(url)

    if response.status_code != 200:
        print("[ERROR] Unable to get release for " + url )

    return response.json()

def getAssetsLinks(assetsObj):
    assetsLinks = {
        "xml": "",
        "zip": ""
    }

    for asset in assetsObj:
        if asset['name'] == 'addon.xml':
            assetsLinks['xml'] = asset['browser_download_url']
            continue

        if asset['name'][-4:] == '.zip':
            assetsLinks['zip'] = asset['browser_download_url']
            continue

    return assetsLinks

def getAddonXML(assertsLinks):
    url = assertsLinks['xml']
    response = requests.get(url)
    root = ET.fromstring(response.content)
    return root

def getAddonZip(assertsLinks, zipFolder):
    url = assertsLinks['zip']
    
    zipName = os.path.basename(url[url.find('/'):])
    zipPath = os.path.join(zipFolder, zipName)
                
    print(f"Downloading {url}")
    r = requests.get(url)
    with open(zipPath, "wb") as f:
        f.write(r.content)


def fetchAndMergeAddons():

    tree = ET.parse(ADDONS_TEMPLATE_PATH)
    root = tree.getroot()

    for addon in ADDONS:
        releaseData = getAddonReleses(addon)
        
        version = releaseData['tag_name']
        assets = getAssetsLinks(releaseData['assets'])

        # Get addon.xml
        xml = getAddonXML(assets)
        addon_id = xml.attrib["id"]
        addon_version = xml.attrib["version"]
        root.append(xml)

        # Create/clean addon folder
        addonFolder = os.path.join(ZIP_DIR, addon_id)
        os.makedirs(addonFolder, exist_ok=True)
        for f in os.listdir(addonFolder):
            os.remove(os.path.join(addonFolder, f))

        # Get matching release ZIP
        getAddonZip(assets, addonFolder)
        
        continue
        releases = requests.get(addon["releases"]).json()
        for rel in releases:
            if rel["tag_name"] == addon_version and rel.get("assets"):
                asset = rel["assets"][0]
                zip_url = asset["browser_download_url"]
                zip_name = asset["name"]
                zip_path = os.path.join(addon_folder, zip_name)

                print(f"Downloading {zip_url}")
                r = requests.get(zip_url)
                with open(zip_path, "wb") as f:
                    f.write(r.content)
                break

    # Save merged addons.xml
    ET.indent(tree, space="  ")
    tree.write(ADDONS_XML_PATH, encoding="utf-8", xml_declaration=True)

    # Generate MD5
    with open(ADDONS_XML_PATH, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    with open(ADDONS_MD5_PATH, "w") as f:
        f.write(md5)

    print("Updated addons.xml and addons.xml.md5")


if __name__ == "__main__":
    addon_id = getAddonId()
    version = getAddonVersion()
    print(f"Building Kodi addon: {addon_id} version {version}")

    cleanBuild()
    fetchAndMergeAddons()    
    createBundle(addon_id, version)
    print("All done.")
import os
import re
import sys
import shutil
import logging

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)

iconpacks_dir = './iconpacks'
drawable_dir = './app/src/main/res/drawable'
arrays_file = './app/src/main/res/values/arrays.xml'
manifest_file = './app/src/main/AndroidManifest.xml'

VALID_DRAWABLE_EXTENSIONS = ['.xml', '.png', '.jpg', '.jpeg', '.webp']


def normalize_package_name(package_name):
    """Normalize specific package names."""
    special_cases = {
        'com.android.systemui': 'systemui',
        'com.android.settings': 'settings'
    }
    return special_cases.get(package_name, package_name)


def get_icon_packs():
    try:
        LOGGER.info("Fetching icon packs from: %s", iconpacks_dir)
        packs = [folder for folder in os.listdir(iconpacks_dir) if os.path.isdir(os.path.join(iconpacks_dir, folder))]
        LOGGER.info("Found %s icon packs.", len(packs))
        return packs
    except Exception as e:
        LOGGER.error("Error fetching icon packs: %s", str(e))
        sys.exit(1)


def replace_drawable_references(content, package_name, pack_name_lower):
    search_pattern = r'@drawable/([a-zA-Z0-9_]+)'
    
    def replace(match):
        drawable_name = match.group(1)
        new_drawable_name = f"{drawable_name}_{package_name}_{pack_name_lower}"
        LOGGER.info("Replacing %s with %s", drawable_name, new_drawable_name)
        return f"@drawable/{new_drawable_name}"

    return re.sub(search_pattern, replace, content)


def update_drawable_references():
    try:
        LOGGER.info("Updating drawable references...")

        for pack_name in get_icon_packs():
            pack_name_lower = re.sub(r'[^a-zA-Z0-9]', '_', pack_name.lower())
            pack_path = os.path.join(iconpacks_dir, pack_name)

            for package_name in os.listdir(pack_path):
                package_path = os.path.join(pack_path, package_name)

                if os.path.isdir(package_path):
                    package_name = normalize_package_name(package_name)

                    for file in os.listdir(package_path):
                        file_extension = os.path.splitext(file)[1].lower()

                        if file_extension in VALID_DRAWABLE_EXTENSIONS:
                            file_path = os.path.join(package_path, file)

                            if file_extension == '.xml':
                                with open(file_path, 'r') as f:
                                    file_content = f.read()

                                updated_content = replace_drawable_references(file_content, package_name, pack_name_lower)

                                if updated_content != file_content:
                                    with open(file_path, 'w') as f:
                                        f.write(updated_content)
                                    
                                    LOGGER.info("Updated drawable references in: %s", file_path)

        LOGGER.info("Drawable references updated successfully.")
    except Exception as e:
        LOGGER.error("Error updating drawable references: %s", str(e))
        sys.exit(1)


def copy_and_rename_files():
    update_drawable_references()

    try:
        LOGGER.info("Starting file copy and rename process...")

        # Ensure the destination directory exists
        if not os.path.exists(drawable_dir):
            os.makedirs(drawable_dir)
            LOGGER.info("Created drawable directory: %s", drawable_dir)

        for pack_name in get_icon_packs():
            pack_name_lower = re.sub(r'[^a-zA-Z0-9]', '_', pack_name.lower())
            pack_path = os.path.join(iconpacks_dir, pack_name)
            LOGGER.info("Processing pack: %s (%s)", pack_name, pack_name_lower)

            for package_name in os.listdir(pack_path):
                package_path = os.path.join(pack_path, package_name)
                if os.path.isdir(package_path):
                    package_name = normalize_package_name(package_name)

                    for file in os.listdir(package_path):
                        file_extension = os.path.splitext(file)[1].lower()

                        if file_extension in VALID_DRAWABLE_EXTENSIONS:
                            original_file_path = os.path.join(package_path, file)
                            new_file_name = f"{os.path.splitext(file)[0]}_{package_name.lower()}_{pack_name_lower}{file_extension}"
                            new_file_path = os.path.join(drawable_dir, new_file_name)

                            LOGGER.info("Copying %s to %s", original_file_path, new_file_path)
                            shutil.copy(original_file_path, new_file_path)

        LOGGER.info("File copy and rename process completed.")
    except Exception as e:
        LOGGER.error("Error in file copy and rename process: %s", str(e))
        sys.exit(1)


def update_manifest():
    try:
        LOGGER.info("Updating manifest file: %s", manifest_file)
        with open(manifest_file, 'r') as f:
            manifest_content = f.read()

        start_comment = '<!-- START OF ICON PACKS -->'
        end_comment = '<!-- END OF ICON PACKS -->'
        start_idx = manifest_content.find(start_comment)
        end_idx = manifest_content.find(end_comment)

        if start_idx == -1 or end_idx == -1:
            LOGGER.error("Error: Comment markers not found in manifest file.")
            sys.exit(1)

        activities = ""
        for pack_name in get_icon_packs():
            pack_name_lower = re.sub(r'[^a-zA-Z0-9]', '_', pack_name.lower())
            activities += f"""
    <activity android:name="{pack_name_lower}"
        android:label="{pack_name}"
        android:exported="true">
        <intent-filter>
            <action android:name="sh.siava.pixelxpert.iconpack" />
            <category android:name="android.intent.category.DEFAULT" />
        </intent-filter>
    </activity>
"""

        new_manifest_content = (
            manifest_content[:start_idx + len(start_comment)] +
            activities +
            manifest_content[end_idx:]
        )

        with open(manifest_file, 'w') as f:
            f.write(new_manifest_content)
        
        LOGGER.info("Manifest file updated successfully.")
    except Exception as e:
        LOGGER.error("Error updating manifest: %s", str(e))
        sys.exit(1)


def update_arrays():
    try:
        LOGGER.info("Updating arrays file: %s", arrays_file)
        with open(arrays_file, 'r') as f:
            arrays_content = f.read()

        start_resources = arrays_content.find('<resources>')
        end_resources = arrays_content.find('</resources>')

        if start_resources == -1 or end_resources == -1:
            LOGGER.error("Error: <resources> tags not found in arrays file.")
            sys.exit(1)

        array_updates = ""

        for pack_name in get_icon_packs():
            pack_name_lower = re.sub(r'[^a-zA-Z0-9]', '_', pack_name.lower())

            array_updates += f"""
<string-array name="{pack_name_lower}">
    <item>mapping_source_{pack_name_lower}</item>
    <item>replacement_{pack_name_lower}</item>
</string-array>
"""

            array_updates += f"""
<string-array name="mapping_source_{pack_name_lower}">
"""
            pack_path = os.path.join(iconpacks_dir, pack_name)
            for package_name in os.listdir(pack_path):
                package_path = os.path.join(pack_path, package_name)

                if os.path.isdir(package_path):
                    for file in os.listdir(package_path):
                        file_extension = os.path.splitext(file)[1].lower()

                        if file_extension in VALID_DRAWABLE_EXTENSIONS:
                            array_updates += f"    <item>{package_name}:{os.path.splitext(file)[0]}</item>\n"
            array_updates += f"</string-array>\n"

            array_updates += f"""
<string-array name="replacement_{pack_name_lower}">
"""
            for package_name in os.listdir(pack_path):
                package_path = os.path.join(pack_path, package_name)

                if os.path.isdir(package_path):
                    package_name = normalize_package_name(package_name)

                    for file in os.listdir(package_path):
                        file_extension = os.path.splitext(file)[1].lower()

                        if file_extension in VALID_DRAWABLE_EXTENSIONS:
                            new_name = f"{os.path.splitext(file)[0]}_{package_name.lower()}_{pack_name_lower}"
                            array_updates += f"    <item>{new_name}</item>\n"
            array_updates += f"</string-array>\n"

        new_arrays_content = arrays_content[:start_resources + len('<resources>')] + array_updates + arrays_content[end_resources:]

        with open(arrays_file, 'w') as f:
            f.write(new_arrays_content)
        
        LOGGER.info("Arrays file updated successfully.")
    except Exception as e:
        LOGGER.error("Error updating arrays file: %s", str(e))
        sys.exit(1)


def main():
    LOGGER.info("Starting the automation process...")
    copy_and_rename_files()
    update_manifest()
    update_arrays()
    LOGGER.info("Automation process completed successfully.")


if __name__ == '__main__':
    LOGGER.info("Python version: %s", sys.version)
    LOGGER.info("Running main logic...")
    main()

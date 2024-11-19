import os
import re
import sys
import shutil

iconpacks_dir = './iconpacks'
drawable_dir = './app/src/main/res/drawable'
arrays_file = './app/src/main/res/values/arrays.xml'
manifest_file = './app/src/main/AndroidManifest.xml'

def get_icon_packs():
    return [folder for folder in os.listdir(iconpacks_dir) if os.path.isdir(os.path.join(iconpacks_dir, folder))]

def copy_and_rename_files():
    for pack_name in get_icon_packs():
        pack_name_lower = re.sub(r'[^a-zA-Z0-9]', '_', pack_name.lower())
        pack_path = os.path.join(iconpacks_dir, pack_name)

        for package_name in os.listdir(pack_path):
            package_path = os.path.join(pack_path, package_name)

            if os.path.isdir(package_path):
                if package_name == 'com.android.systemui':
                    package_name = 'systemui'
                elif package_name == 'com.android.settings':
                    package_name = 'settings'

                for file in os.listdir(package_path):
                    file_extension = os.path.splitext(file)[1].lower()

                    if file_extension in ['.xml', '.png', '.jpg', '.jpeg']:
                        original_file_path = os.path.join(package_path, file)
                        new_file_name = f"{os.path.splitext(file)[0]}_{package_name.lower()}_{pack_name_lower}{file_extension}"
                        new_file_path = os.path.join(drawable_dir, new_file_name)
                        shutil.copy(original_file_path, new_file_path)

def update_manifest():
    with open(manifest_file, 'r') as f:
        manifest_content = f.read()

    start_comment = '<!-- START OF ICON PACKS -->'
    end_comment = '<!-- END OF ICON PACKS -->'
    start_idx = manifest_content.find(start_comment)
    end_idx = manifest_content.find(end_comment)

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

def update_arrays():
    with open(arrays_file, 'r') as f:
        arrays_content = f.read()

    start_resources = arrays_content.find('<resources>')
    end_resources = arrays_content.find('</resources>')

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

                    if file_extension in ['.xml', '.png', '.jpg', '.jpeg']:
                        array_updates += f"    <item>{package_name}:{os.path.splitext(file)[0]}</item>\n"
        array_updates += f"</string-array>\n"

        array_updates += f"""
<string-array name="replacement_{pack_name_lower}">
"""
        for package_name in os.listdir(pack_path):
            package_path = os.path.join(pack_path, package_name)

            if os.path.isdir(package_path):
                if package_name == 'com.android.systemui':
                    package_name = 'systemui'
                elif package_name == 'com.android.settings':
                    package_name = 'settings'

                for file in os.listdir(package_path):
                    file_extension = os.path.splitext(file)[1].lower()

                    if file_extension in ['.xml', '.png', '.jpg', '.jpeg']:
                        new_name = f"{os.path.splitext(file)[0]}_{package_name.lower()}_{pack_name_lower}"
                        array_updates += f"    <item>{new_name}</item>\n"
        array_updates += f"</string-array>\n"

    new_arrays_content = arrays_content[:start_resources + len('<resources>')] + array_updates + arrays_content[end_resources:]

    with open(arrays_file, 'w') as f:
        f.write(new_arrays_content)

def main():
    copy_and_rename_files()
    update_manifest()
    update_arrays()

if __name__ == '__main__':
    print(f"Python version: {sys.version}")
    print("Running main logic...")
    main()

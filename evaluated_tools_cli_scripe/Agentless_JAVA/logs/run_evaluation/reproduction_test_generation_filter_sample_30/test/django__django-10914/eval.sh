#!/bin/bash
set -uxo pipefail
source /opt/miniconda3/bin/activate
conda activate testbed
cd /testbed
sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
export LANG=en_US.UTF-8
export LANGUAGE=en_US:en
export LC_ALL=en_US.UTF-8
git config --global --add safe.directory /testbed
cd /testbed
git status
git show
git diff e7fd69d051eaa67cb17f172a39b57253e9cb831a
source /opt/miniconda3/bin/activate
conda activate testbed
python -m pip install -e .
git checkout e7fd69d051eaa67cb17f172a39b57253e9cb831a
git apply -v - <<'EOF_114329324912'
diff --git a/this_is_invisible_2.py b/this_is_invisible_2.py
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/this_is_invisible_2.py
@@ -0,0 +1 @@
+# This is a commented out line

EOF_114329324912
git apply -v - <<'EOF_114329324912'
diff --git a/reproduce_bug.py b/reproduce_bug.py
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/reproduce_bug.py
@@ -0,0 +1,47 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions():
+    # Define the content and name of the uploaded file
+    file_content = b"dummy content"
+    file_name = "testfile.txt"
+
+    # Create a SimpleUploadedFile instance
+    simple_uploaded_file = SimpleUploadedFile(file_name, file_content)
+
+    # Create a TemporaryUploadedFile instance
+    temp_uploaded_file = TemporaryUploadedFile(file_name, 'text/plain', len(file_content), 'UTF-8')
+
+    # Write the content to the TemporaryUploadedFile
+    temp_uploaded_file.write(file_content)
+    temp_uploaded_file.seek(0)
+
+    # Set up FileSystemStorage
+    storage = FileSystemStorage()
+
+    # Save the file using FileSystemStorage
+    saved_file_path_simple = storage.save(file_name, simple_uploaded_file)
+    saved_file_path_temp = storage.save(f"temp_{file_name}", temp_uploaded_file)
+
+    # Retrieve the file permissions
+    simple_file_permissions = oct(os.stat(saved_file_path_simple).st_mode & 0o777)
+    temp_file_permissions = oct(os.stat(saved_file_path_temp).st_mode & 0o777)
+
+    # Clean up created files
+    storage.delete(saved_file_path_simple)
+    storage.delete(saved_file_path_temp)
+
+    # Check and print results
+    expected_permissions = '0o644'
+
+    if simple_file_permissions == expected_permissions and temp_file_permissions == expected_permissions:
+        print("Issue resolved")
+    elif simple_file_permissions == '0o600' or temp_file_permissions == '0o600':
+        print("Issue reproduced")
+    else:
+        print("Other issues")
+
+# Run the test
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

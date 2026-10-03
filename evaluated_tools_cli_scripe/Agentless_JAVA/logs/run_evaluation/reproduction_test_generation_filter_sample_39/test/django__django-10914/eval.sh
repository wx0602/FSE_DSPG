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
@@ -0,0 +1,58 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import TemporaryUploadedFile, InMemoryUploadedFile
+from django.core.files.storage import FileSystemStorage
+from io import BytesIO
+
+def test_file_upload_permissions():
+    # Create a temporary directory to act as the file storage location
+    with tempfile.TemporaryDirectory() as tmp_dir:
+        storage = FileSystemStorage(location=tmp_dir)
+
+        # Create a TemporaryUploadedFile
+        temp_file = tempfile.NamedTemporaryFile(delete=False)
+        temp_file.write(b"Temporary file content")
+        temp_file.seek(0)
+        uploaded_file = TemporaryUploadedFile(temp_file.name, 'text/plain', temp_file.tell(), 'utf-8')
+
+        # Save the TemporaryUploadedFile
+        saved_name = storage.save('uploaded_tempfile.txt', uploaded_file)
+        saved_path = storage.path(saved_name)
+
+        # Check the permissions of the saved file
+        permissions = oct(os.stat(saved_path).st_mode & 0o777)
+        print(f"TemporaryUploadedFile permissions: {permissions}")
+
+        # Check for the issue
+        if permissions == '0o600':
+            print("Issue reproduced")
+        else:
+            print("Issue resolved")
+
+        # Cleanup
+        os.remove(saved_path)
+
+        # Create an InMemoryUploadedFile
+        in_memory_file = BytesIO(b"In-memory file content")
+        uploaded_file = InMemoryUploadedFile(in_memory_file, None, 'uploaded_inmemoryfile.txt', 'text/plain', in_memory_file.tell(), 'utf-8')
+
+        # Save the InMemoryUploadedFile
+        saved_name = storage.save('uploaded_inmemoryfile.txt', uploaded_file)
+        saved_path = storage.path(saved_name)
+
+        # Check the permissions of the saved file
+        permissions = oct(os.stat(saved_path).st_mode & 0o777)
+        print(f"InMemoryUploadedFile permissions: {permissions}")
+
+        # Check for the issue
+        if permissions == '0o600':
+            print("Issue reproduced")
+        elif permissions == '0o644':
+            print("Issue resolved")
+        else:
+            print("Other issues")
+
+        # Cleanup
+        os.remove(saved_path)
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

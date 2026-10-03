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
@@ -0,0 +1,45 @@
+import os
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions():
+    try:
+        # Set up the file storage
+        storage = FileSystemStorage(location='/tmp')
+
+        # Simulate a small file upload (MemoryUploadedFile)
+        small_file = SimpleUploadedFile("small_file.txt", b"Small file content")
+        small_file_name = storage.save(small_file.name, small_file)
+
+        # Check permissions of the small file
+        small_file_path = os.path.join('/tmp', small_file_name)
+        small_file_permissions = oct(os.stat(small_file_path).st_mode & 0o777)
+
+        # Simulate a large file upload (TemporaryUploadedFile)
+        large_file = TemporaryUploadedFile("large_file.txt", "text/plain", 1024**2, "utf-8")
+        large_file.write(b"Large file content" * 1024)
+        large_file.seek(0)  # Reset file pointer to the beginning
+
+        large_file_name = storage.save(large_file.name, large_file)
+
+        # Check permissions of the large file
+        large_file_path = os.path.join('/tmp', large_file_name)
+        large_file_permissions = oct(os.stat(large_file_path).st_mode & 0o777)
+
+        # Clean up created files
+        os.remove(small_file_path)
+        os.remove(large_file_path)
+
+        # Check and assert the permissions
+        if small_file_permissions == '0o644' and large_file_permissions == '0o644':
+            print("Issue resolved")
+        elif small_file_permissions == '0o644' and large_file_permissions == '0o600':
+            print("Issue reproduced")
+        else:
+            print("Other issues")
+
+    except Exception as e:
+        print("Other issues")
+        print(e)
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

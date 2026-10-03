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
@@ -0,0 +1,41 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions():
+    # Create a temporary directory to act as MEDIA_ROOT
+    temp_dir = tempfile.mkdtemp()
+    storage = FileSystemStorage(location=temp_dir)
+
+    # Simulate a file upload using SimpleUploadedFile (small file)
+    small_file = SimpleUploadedFile("small_test_file.txt", b"Small file content")
+    small_file_path = storage.save("small_test_file.txt", small_file)
+    small_file_full_path = os.path.join(temp_dir, small_file_path)
+
+    # Simulate a file upload using TemporaryUploadedFile (large file, exceeding size limit)
+    temp_file = tempfile.NamedTemporaryFile(delete=False)
+    temp_file.write(b"Large file content" * 1024)  # Make sure the file is large enough
+    temp_file.seek(0)
+    large_file = TemporaryUploadedFile(temp_file.name, "text/plain", 1024 * 1024, "UTF-8")
+    large_file_path = storage.save("large_test_file.txt", large_file)
+    large_file_full_path = os.path.join(temp_dir, large_file_path)
+
+    # Check permissions of the small file
+    small_file_permissions = oct(os.stat(small_file_full_path).st_mode & 0o777)
+    # Check permissions of the large file
+    large_file_permissions = oct(os.stat(large_file_full_path).st_mode & 0o777)
+
+    if small_file_permissions == '0o644' and large_file_permissions == '0o644':
+        print("Issue resolved")
+    elif small_file_permissions != '0o644' or large_file_permissions != '0o644':
+        print("Issue reproduced")
+    else:
+        print("Other issues")
+
+    # Clean up temporary files
+    os.remove(small_file_full_path)
+    os.remove(large_file_full_path)
+    os.rmdir(temp_dir)
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

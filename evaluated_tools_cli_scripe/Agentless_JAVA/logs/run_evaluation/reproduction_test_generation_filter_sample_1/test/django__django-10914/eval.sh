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
@@ -0,0 +1,40 @@
+import os
+import tempfile
+from django.core.files.storage import FileSystemStorage
+from django.core.files.uploadedfile import SimpleUploadedFile
+
+def test_file_upload_permissions():
+    # Setup a temporary directory for file storage
+    with tempfile.TemporaryDirectory() as temp_dir:
+        storage = FileSystemStorage(location=temp_dir)
+
+        # Create a small file to upload (this will be a MemoryUploadedFile)
+        small_file = SimpleUploadedFile("small_test_file.txt", b"small file content")
+
+        # Save the uploaded file using FileSystemStorage
+        saved_file_path = storage.save(small_file.name, small_file)
+
+        # Check the permissions of the saved file
+        small_file_permissions = os.stat(os.path.join(temp_dir, small_file.name)).st_mode & 0o777
+
+        # Create a large file to upload to force TemporaryUploadedFile usage
+        large_file_content = b"x" * (2 * 1024 * 1024)  # 2MB file
+        large_file = SimpleUploadedFile("large_test_file.txt", large_file_content)
+        
+        # Save the uploaded file using FileSystemStorage
+        saved_large_file_path = storage.save(large_file.name, large_file)
+
+        # Check the permissions of the saved large file
+        large_file_permissions = os.stat(os.path.join(temp_dir, large_file.name)).st_mode & 0o777
+
+        try:
+            # Check if both files have the same permissions
+            assert small_file_permissions == large_file_permissions == 0o644
+            print("Issue resolved")
+        except AssertionError:
+            if small_file_permissions != 0o644 or large_file_permissions != 0o644:
+                print("Issue reproduced")
+            else:
+                print("Other issues")
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

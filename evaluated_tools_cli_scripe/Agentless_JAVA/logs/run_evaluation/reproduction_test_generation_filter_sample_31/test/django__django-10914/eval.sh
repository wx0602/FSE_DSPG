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
@@ -0,0 +1,44 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions():
+    try:
+        # Set up a simple file storage
+        storage = FileSystemStorage(location=tempfile.mkdtemp())
+
+        # Create a small file and a large file
+        small_file = SimpleUploadedFile("small_file.txt", b"small file content")
+        large_file_path = tempfile.mktemp()
+        with open(large_file_path, 'wb') as f:
+            f.write(b"large file content" * 1024)  # Make it large enough to be a TemporaryUploadedFile
+
+        large_file = TemporaryUploadedFile(name="large_file.txt",
+                                           content_type="text/plain",
+                                           size=os.path.getsize(large_file_path),
+                                           charset='utf-8')
+
+        # Save files to storage
+        small_file_name = storage.save("small_file.txt", small_file)
+        large_file_name = storage.save("large_file.txt", large_file)
+
+        # Get the file paths
+        small_file_path = storage.path(small_file_name)
+        large_file_path = storage.path(large_file_name)
+
+        # Check file permissions
+        small_file_permissions = oct(os.stat(small_file_path).st_mode & 0o777)
+        large_file_permissions = oct(os.stat(large_file_path).st_mode & 0o777)
+
+        # Determine if the issue is reproduced or resolved
+        if small_file_permissions == '0o644' and large_file_permissions == '0o644':
+            print("Issue resolved")
+        elif small_file_permissions != '0o644' or large_file_permissions != '0o644':
+            print("Issue reproduced")
+        else:
+            print("Other issues")
+    except Exception as e:
+        print(f"Other issues: {str(e)}")
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

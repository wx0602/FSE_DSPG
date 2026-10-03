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
@@ -0,0 +1,38 @@
+import os
+from tempfile import NamedTemporaryFile
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions():
+    # Set up the file storage
+    storage = FileSystemStorage(location='/tmp')
+
+    # Create a simple uploaded file (small size, will use MemoryUploadedFile)
+    simple_file = SimpleUploadedFile("simple_file.txt", b"Simple file content")
+    simple_file_path = storage.save("simple_file.txt", simple_file)
+
+    # Create a temporary uploaded file (larger size, will use TemporaryUploadedFile)
+    temp_file = TemporaryUploadedFile("temp_file.txt", "text/plain", 1024, "utf-8")
+    temp_file_path = storage.save("temp_file.txt", temp_file)
+
+    # Get the permissions of the saved files
+    simple_file_permissions = oct(os.stat(storage.path(simple_file_path)).st_mode & 0o777)
+    temp_file_permissions = oct(os.stat(storage.path(temp_file_path)).st_mode & 0o777)
+
+    # Clean up the files
+    os.remove(storage.path(simple_file_path))
+    os.remove(storage.path(temp_file_path))
+
+    # Check if the permissions are as expected
+    try:
+        assert simple_file_permissions == '0o644', f"Expected 0o644, but got {simple_file_permissions}"
+        assert temp_file_permissions == '0o644', f"Expected 0o644, but got {temp_file_permissions}"
+        print("Issue resolved")
+    except AssertionError as e:
+        if '0o600' in str(e):
+            print("Issue reproduced")
+        else:
+            print("Other issues")
+        return
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

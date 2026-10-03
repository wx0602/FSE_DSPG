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
@@ -0,0 +1,43 @@
+import os
+from tempfile import NamedTemporaryFile
+from django.core.files.storage import FileSystemStorage
+from django.conf import settings
+
+# Ensure settings are configured for the test
+settings.configure(
+    DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage',
+    FILE_UPLOAD_HANDLERS=[
+        'django.core.files.uploadhandler.MemoryFileUploadHandler',
+        'django.core.files.uploadhandler.TemporaryFileUploadHandler',
+    ]
+)
+
+def test_file_upload_permissions():
+    fs = FileSystemStorage(location='/tmp')
+
+    # Create a temporary file to simulate an uploaded file
+    with NamedTemporaryFile(delete=True) as temp_file:
+        temp_file.write(b'Test file content')
+        temp_file.flush()
+
+        # Save the file using FileSystemStorage
+        file_name = fs.save('testfile.txt', temp_file)
+
+    # Get the full path of the saved file
+    file_path = fs.path(file_name)
+
+    try:
+        # Check the file permissions
+        file_permissions = oct(os.stat(file_path).st_mode & 0o777)
+        
+        if file_permissions == '0o600':
+            print("Issue reproduced")
+        elif file_permissions == '0o644':
+            print("Issue resolved")
+        else:
+            print("Other issues")
+    finally:
+        # Clean up the file after the test
+        os.remove(file_path)
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

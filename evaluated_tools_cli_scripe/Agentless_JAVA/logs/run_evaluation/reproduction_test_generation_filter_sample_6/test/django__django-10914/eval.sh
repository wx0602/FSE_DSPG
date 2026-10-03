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
@@ -0,0 +1,52 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+from django.core.files.storage import FileSystemStorage
+from django.conf import settings
+
+def test_file_upload_permission_issue():
+    # Setup Django settings for FILE_UPLOAD_HANDLERS and FILE_UPLOAD_PERMISSIONS
+    settings.configure(
+        FILE_UPLOAD_HANDLERS=[
+            'django.core.files.uploadhandler.MemoryFileUploadHandler',
+            'django.core.files.uploadhandler.TemporaryFileUploadHandler',
+        ],
+        FILE_UPLOAD_PERMISSIONS=None,
+        DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage',
+    )
+
+    # Create a temporary file using TemporaryUploadedFile to simulate large file upload
+    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
+        temp_file.write(b"dummy data" * 1024 * 1024)  # Write 1MB of data to ensure it uses TemporaryUploadedFile
+        temp_file_path = temp_file.name
+
+    uploaded_file = TemporaryUploadedFile(
+        name=os.path.basename(temp_file_path),
+        content_type='text/plain',
+        size=os.path.getsize(temp_file_path),
+        charset='utf-8'
+    )
+    uploaded_file.file = open(temp_file_path, 'rb')
+
+    # Use FileSystemStorage to save the uploaded file
+    storage = FileSystemStorage()
+    saved_file_name = storage.save(uploaded_file.name, uploaded_file)
+    saved_file_path = storage.path(saved_file_name)
+
+    # Check the permissions of the saved file
+    saved_file_permissions = oct(os.stat(saved_file_path).st_mode & 0o777)
+
+    # Clean up the temporary file and uploaded file
+    uploaded_file.close()
+    os.remove(temp_file_path)
+    os.remove(saved_file_path)
+
+    # Print results based on the file permissions
+    if saved_file_permissions == '0o644':
+        print("Issue resolved")
+    elif saved_file_permissions == '0o600':
+        print("Issue reproduced")
+    else:
+        print("Other issues")
+
+test_file_upload_permission_issue()

EOF_114329324912
python3 reproduce_bug.py

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
@@ -0,0 +1,48 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import SimpleUploadedFile
+from django.core.files.storage import FileSystemStorage
+from django.conf import settings
+
+def test_file_upload_permissions():
+    # Set up Django settings required for file uploads
+    settings.configure(
+        DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage',
+        FILE_UPLOAD_HANDLERS=[
+            'django.core.files.uploadhandler.MemoryFileUploadHandler',
+            'django.core.files.uploadhandler.TemporaryFileUploadHandler'
+        ]
+    )
+
+    storage = FileSystemStorage()
+
+    # Create a temporary file to simulate file upload
+    temp_file = tempfile.NamedTemporaryFile(delete=False)
+    temp_file.write(b'Test file content')
+    temp_file.seek(0)
+    temp_file_name = temp_file.name
+    temp_file.close()
+
+    uploaded_file = SimpleUploadedFile(name='testfile.txt', content=open(temp_file_name, 'rb').read())
+
+    # Save the uploaded file using FileSystemStorage
+    saved_path = storage.save('uploaded_testfile.txt', uploaded_file)
+
+    # Get the actual file path
+    full_path = os.path.join(storage.location, saved_path)
+
+    # Check the file permissions
+    file_permissions = oct(os.stat(full_path).st_mode & 0o777)
+
+    # Clean up by deleting the uploaded file
+    os.remove(full_path)
+
+    # Check the outcome
+    if file_permissions == '0o644':
+        print("Issue resolved")
+    elif file_permissions == '0o600':
+        print("Issue reproduced")
+    else:
+        print("Other issues")
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

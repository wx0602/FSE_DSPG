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
+from django.core.files.uploadedfile import SimpleUploadedFile
+from django.core.files.storage import FileSystemStorage
+from django.conf import settings
+
+def test_file_upload_permissions():
+    # Setup Django settings if not already configured
+    if not settings.configured:
+        settings.configure(
+            FILE_UPLOAD_HANDLERS=[
+                'django.core.files.uploadhandler.MemoryFileUploadHandler',
+                'django.core.files.uploadhandler.TemporaryFileUploadHandler',
+            ],
+            FILE_UPLOAD_PERMISSIONS=None,  # Ensuring that FILE_UPLOAD_PERMISSIONS is not set
+            MEDIA_ROOT=tempfile.gettempdir(),  # Using temp directory for media root
+            MEDIA_URL='/media/',
+        )
+
+    # Create a file to upload
+    uploaded_file = SimpleUploadedFile("testfile.txt", b"Test content")
+
+    # Use FileSystemStorage to save the uploaded file
+    storage = FileSystemStorage()
+    saved_path = storage.save("testfile.txt", uploaded_file)
+    saved_file_path = os.path.join(settings.MEDIA_ROOT, saved_path)
+
+    try:
+        # Check the file permissions
+        file_permissions = oct(os.stat(saved_file_path).st_mode & 0o777)
+        expected_permissions = "0o644"
+
+        if file_permissions == expected_permissions:
+            print("Issue resolved")
+        else:
+            print(f"Issue reproduced - Permissions are {file_permissions}")
+    except Exception as e:
+        print(f"Other issues - {e}")
+    finally:
+        # Clean up the uploaded file
+        if os.path.exists(saved_file_path):
+            os.remove(saved_file_path)
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

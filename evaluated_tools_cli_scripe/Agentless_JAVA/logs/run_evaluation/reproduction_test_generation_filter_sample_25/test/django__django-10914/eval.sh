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
+import tempfile
+from django.core.files.uploadedfile import SimpleUploadedFile
+from django.core.files.storage import FileSystemStorage
+from django.conf import settings
+
+def test_file_upload_permission_issue():
+    # Setup: Configure Django settings for the test
+    settings.configure(
+        DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage',
+        FILE_UPLOAD_HANDLERS=[
+            'django.core.files.uploadhandler.MemoryFileUploadHandler',
+            'django.core.files.uploadhandler.TemporaryFileUploadHandler',
+        ]
+    )
+
+    # Create a temporary directory for file storage
+    with tempfile.TemporaryDirectory() as tmp_dir:
+        storage = FileSystemStorage(location=tmp_dir)
+        
+        # Create a temporary uploaded file
+        uploaded_file = SimpleUploadedFile(
+            name='test.txt',
+            content=b'This is some test content.',
+            content_type='text/plain'
+        )
+        
+        # Save the file using FileSystemStorage
+        saved_path = storage.save('test.txt', uploaded_file)
+        saved_file_path = os.path.join(tmp_dir, saved_path)
+        
+        # Check file permissions
+        file_permissions = oct(os.stat(saved_file_path).st_mode & 0o777)
+        
+        # Reproduce the issue
+        if file_permissions != '0o644':
+            print("Issue reproduced")
+        else:
+            print("Issue resolved")
+    except Exception as e:
+        print("Other issues")
+        print(e)
+
+# Run the test
+test_file_upload_permission_issue()

EOF_114329324912
python3 reproduce_bug.py

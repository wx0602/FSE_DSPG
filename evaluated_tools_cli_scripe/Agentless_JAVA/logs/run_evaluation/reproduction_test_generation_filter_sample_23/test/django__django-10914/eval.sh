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
+from django.core.files.uploadedfile import SimpleUploadedFile
+from django.core.files.storage import FileSystemStorage
+from django.conf import settings
+
+def test_file_upload_permissions():
+    # Set up a temporary storage location for testing
+    test_storage_location = 'test_storage'
+    os.makedirs(test_storage_location, exist_ok=True)
+    test_storage = FileSystemStorage(location=test_storage_location)
+
+    # Define a simple uploaded file
+    test_file_content = b"Test content"
+    test_file = SimpleUploadedFile("test_file.txt", test_file_content)
+
+    # Save the file using the storage system
+    saved_file_path = test_storage.save(test_file.name, test_file)
+
+    # Get the full path to the saved file
+    full_saved_file_path = os.path.join(test_storage_location, saved_file_path)
+
+    # Check the file permissions
+    file_permissions = oct(os.stat(full_saved_file_path).st_mode & 0o777)
+
+    # Clean up - remove the saved file and directory
+    os.remove(full_saved_file_path)
+    os.rmdir(test_storage_location)
+
+    # Check if the issue is reproduced or resolved
+    if file_permissions == '0o600':
+        print("Issue reproduced")
+    elif file_permissions == '0o644':
+        print("Issue resolved")
+    else:
+        print("Other issues")
+    
+# Ensure that the necessary Django settings are configured for the test
+settings.configure(
+    FILE_UPLOAD_HANDLERS=['django.core.files.uploadhandler.MemoryFileUploadHandler', 
+                          'django.core.files.uploadhandler.TemporaryFileUploadHandler'],
+    FILE_UPLOAD_PERMISSIONS=0o644,  # This line can be commented out to reproduce the issue
+)
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

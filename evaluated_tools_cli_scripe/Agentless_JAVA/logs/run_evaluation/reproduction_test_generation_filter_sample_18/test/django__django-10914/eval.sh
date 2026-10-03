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
+
+def test_file_upload_permissions_issue():
+    # Setup the test environment
+    storage = FileSystemStorage()
+    upload_dir = storage.location
+    file_content = b'Test file content'
+    file_name = 'test_file.txt'
+
+    # Create a simple uploaded file (this simulates a small file, in-memory storage)
+    simple_file = SimpleUploadedFile(file_name, file_content)
+
+    # Save the file using FileSystemStorage
+    simple_file_path = storage.save(file_name, simple_file)
+    simple_file_full_path = os.path.join(upload_dir, simple_file_path)
+
+    # Check permissions of the file saved with SimpleUploadedFile
+    simple_file_permissions = oct(os.stat(simple_file_full_path).st_mode & 0o777)
+    
+    # Remove the file to clean up
+    os.remove(simple_file_full_path)
+
+    # Create a temporary uploaded file (this simulates a large file, disk-based storage)
+    temp_file = TemporaryUploadedFile(file_name, 'text/plain', len(file_content), 'utf-8')
+    temp_file.file.write(file_content)
+    temp_file.file.seek(0)
+
+    # Save the file using FileSystemStorage
+    temp_file_path = storage.save(file_name, temp_file)
+    temp_file_full_path = os.path.join(upload_dir, temp_file_path)
+
+    # Check permissions of the file saved with TemporaryUploadedFile
+    temp_file_permissions = oct(os.stat(temp_file_full_path).st_mode & 0o777)
+    
+    # Remove the file to clean up
+    os.remove(temp_file_full_path)
+
+    # Determine if the issue is reproduced or resolved
+    if simple_file_permissions == '0o644' and temp_file_permissions == '0o600':
+        print("Issue reproduced")
+    elif simple_file_permissions == '0o644' and temp_file_permissions == '0o644':
+        print("Issue resolved")
+    else:
+        print("Other issues")
+
+    return
+
+# Run the test
+test_file_upload_permissions_issue()

EOF_114329324912
python3 reproduce_bug.py

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
@@ -0,0 +1,50 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions():
+    # Create a temporary file to simulate a file upload
+    temp_file = tempfile.NamedTemporaryFile(delete=False)
+    try:
+        # Initialize FileSystemStorage
+        storage = FileSystemStorage()
+
+        # Create a SimpleUploadedFile with small size to simulate MemoryUploadedFile
+        small_file = SimpleUploadedFile('small_file.txt', b'Hello World')
+
+        # Save the small file using FileSystemStorage
+        small_file_path = storage.save('small_file.txt', small_file)
+        small_file_full_path = os.path.join(storage.location, small_file_path)
+
+        # Check the permissions of the small file
+        small_file_permissions = oct(os.stat(small_file_full_path).st_mode & 0o777)
+        
+        # Remove the small file
+        os.remove(small_file_full_path)
+
+        # Create a TemporaryUploadedFile to simulate larger file upload
+        large_file = TemporaryUploadedFile('large_file.txt', 'text/plain', 0, 'UTF-8')
+
+        # Save the large file using FileSystemStorage
+        large_file_path = storage.save('large_file.txt', large_file)
+        large_file_full_path = os.path.join(storage.location, large_file_path)
+
+        # Check the permissions of the large file
+        large_file_permissions = oct(os.stat(large_file_full_path).st_mode & 0o777)
+        
+        # Remove the large file
+        os.remove(large_file_full_path)
+
+        # Compare the permissions and print the appropriate message
+        if small_file_permissions == '0o644' and large_file_permissions == '0o644':
+            print("Issue resolved")
+        elif small_file_permissions == large_file_permissions:
+            print("Issue reproduced")
+        else:
+            print("Other issues")
+    finally:
+        # Ensure the temporary file is removed
+        os.remove(temp_file.name)
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

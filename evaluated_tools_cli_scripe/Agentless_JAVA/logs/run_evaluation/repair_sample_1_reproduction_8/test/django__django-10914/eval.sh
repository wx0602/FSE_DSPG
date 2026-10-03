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
@@ -0,0 +1,54 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+from django.conf import settings
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions():
+    # Setting up test environment
+    settings.configure()
+    
+    # Create a FileSystemStorage instance
+    storage = FileSystemStorage()
+
+    # Create a simple uploaded file
+    uploaded_file = SimpleUploadedFile("test_file.txt", b"file_content")
+    
+    # Save the uploaded file using FileSystemStorage
+    storage.save("simple_uploaded_file.txt", uploaded_file)
+    
+    # Check the file permissions
+    simple_file_path = storage.path("simple_uploaded_file.txt")
+    simple_file_permissions = oct(os.stat(simple_file_path).st_mode & 0o777)
+
+    # Create a temporary uploaded file
+    temp_file = TemporaryUploadedFile("temp_file.txt", "text/plain", 100, "utf-8")
+    temp_file.write(b"temporary_content")
+    temp_file.seek(0)
+
+    # Save the temporary uploaded file using FileSystemStorage
+    storage.save("temporary_uploaded_file.txt", temp_file)
+
+    # Check the file permissions
+    temp_file_path = storage.path("temporary_uploaded_file.txt")
+    temp_file_permissions = oct(os.stat(temp_file_path).st_mode & 0o777)
+    
+    # Clean up created files
+    os.remove(simple_file_path)
+    os.remove(temp_file_path)
+    
+    try:
+        # Expected permissions
+        expected_permissions = '0o644'
+        
+        # Check if the permissions are as expected
+        assert simple_file_permissions == expected_permissions, f"Simple file permissions: {simple_file_permissions}"
+        assert temp_file_permissions == expected_permissions, f"Temporary file permissions: {temp_file_permissions}"
+        print("Issue resolved")
+    except AssertionError as e:
+        if '0o600' in str(e):
+            print("Issue reproduced")
+        else:
+            print("Other issues")
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

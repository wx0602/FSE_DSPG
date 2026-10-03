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
@@ -0,0 +1,36 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import SimpleUploadedFile
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions():
+    # Create a temporary directory to act as the file storage location
+    with tempfile.TemporaryDirectory() as temp_dir:
+        # Set up the FileSystemStorage to use the temporary directory
+        storage = FileSystemStorage(location=temp_dir)
+
+        # Simulate an uploaded file
+        uploaded_file = SimpleUploadedFile("testfile.txt", b"file_content")
+
+        # Save the file using the storage system
+        saved_path = storage.save("testfile.txt", uploaded_file)
+
+        # Get the full path of the saved file
+        full_path = os.path.join(temp_dir, saved_path)
+
+        # Check the file permissions
+        file_permissions = oct(os.stat(full_path).st_mode & 0o777)
+
+        try:
+            # Verify the file permissions
+            if file_permissions == '0o600':
+                print("Issue reproduced")
+            elif file_permissions == '0o644':
+                print("Issue resolved")
+            else:
+                print("Other issues")
+        except Exception as e:
+            print(f"Other issues: {e}")
+
+# Call the test function
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

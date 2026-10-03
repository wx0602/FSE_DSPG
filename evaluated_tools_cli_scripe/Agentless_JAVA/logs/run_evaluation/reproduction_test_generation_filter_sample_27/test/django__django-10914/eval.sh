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
@@ -0,0 +1,47 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions_issue():
+    try:
+        # Create a temporary directory to simulate file storage
+        with tempfile.TemporaryDirectory() as temp_dir:
+
+            # Initialize FileSystemStorage with the temporary directory
+            storage = FileSystemStorage(location=temp_dir)
+
+            # Create a small file to use SimpleUploadedFile
+            small_file = SimpleUploadedFile('small_test_file.txt', b'Test content')
+
+            # Save the small file
+            storage.save(small_file.name, small_file)
+
+            # Check the permissions of the saved small file
+            small_file_path = os.path.join(temp_dir, small_file.name)
+            small_file_permissions = oct(os.stat(small_file_path).st_mode & 0o777)
+
+            # Create a large file to use TemporaryUploadedFile
+            large_file = TemporaryUploadedFile('large_test_file.txt', 'text/plain', 10**6, 'utf-8')
+
+            # Write content to the large file
+            large_file.write(b'Test content' * 125000)  # Writing 1 MB of content
+            large_file.seek(0)
+
+            # Save the large file
+            storage.save(large_file.name, large_file)
+
+            # Check the permissions of the saved large file
+            large_file_path = os.path.join(temp_dir, large_file.name)
+            large_file_permissions = oct(os.stat(large_file_path).st_mode & 0o777)
+
+            # Determine if the issue is reproduced or resolved
+            if small_file_permissions != '0o644' or large_file_permissions != '0o644':
+                print("Issue reproduced")
+            else:
+                print("Issue resolved")
+
+    except Exception as e:
+        print("Other issues:", e)
+
+test_file_upload_permissions_issue()

EOF_114329324912
python3 reproduce_bug.py

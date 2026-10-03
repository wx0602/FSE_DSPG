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
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions():
+    try:
+        # Mock upload handler and storage
+        storage = FileSystemStorage()
+        
+        # Create a temporary file to simulate file upload
+        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
+            temp_file.write(b"Sample file content")
+            temp_file.flush()
+            temp_file_name = temp_file.name
+
+        # Simulate file upload through TemporaryUploadedFile
+        uploaded_file = TemporaryUploadedFile(
+            name=os.path.basename(temp_file_name),
+            content_type='text/plain',
+            size=os.path.getsize(temp_file_name),
+            charset='utf-8'
+        )
+        
+        # Save the file using the storage backend
+        saved_file_path = storage.save(uploaded_file.name, uploaded_file)
+        
+        # Check file permissions
+        file_permissions = oct(os.stat(saved_file_path).st_mode & 0o777)
+        
+        # Clean up
+        os.remove(saved_file_path)
+        os.remove(temp_file_name)
+
+        # Determine the result
+        if file_permissions == '0o600':
+            print("Issue reproduced")
+        else:
+            print("Issue resolved")
+    except Exception as e:
+        print("Other issues")
+        print(str(e))
+
+# Run the test
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

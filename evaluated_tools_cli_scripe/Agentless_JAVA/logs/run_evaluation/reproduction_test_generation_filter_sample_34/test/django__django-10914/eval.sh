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
@@ -0,0 +1,51 @@
+import os
+from tempfile import NamedTemporaryFile
+from django.core.files.storage import FileSystemStorage
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+
+# Test function to reproduce the issue and verify if it's resolved
+def test_file_upload_permissions():
+    # Setup FileSystemStorage
+    storage = FileSystemStorage(location='/tmp')
+
+    # Create a temporary file using NamedTemporaryFile to simulate file upload
+    with NamedTemporaryFile(delete=False) as temp_file:
+        temp_file.write(b"Test content")
+        temp_file.flush()
+        temp_file_name = temp_file.name
+
+    # Simulate file upload using SimpleUploadedFile and TemporaryUploadedFile
+    simple_file = SimpleUploadedFile('simple_file.txt', b'Test content')
+    temp_uploaded_file = TemporaryUploadedFile(temp_file_name, 'text/plain', len(b'Test content'), 'utf-8')
+
+    # Save files to storage
+    saved_simple_file = storage.save('simple_file.txt', simple_file)
+    saved_temp_file = storage.save('temp_file.txt', temp_uploaded_file)
+
+    # Get the file paths of the saved files
+    simple_file_path = os.path.join(storage.location, saved_simple_file)
+    temp_file_path = os.path.join(storage.location, saved_temp_file)
+
+    # Get file permissions
+    simple_file_permissions = oct(os.stat(simple_file_path).st_mode & 0o777)
+    temp_file_permissions = oct(os.stat(temp_file_path).st_mode & 0o777)
+
+    # Clean up created files
+    os.remove(simple_file_path)
+    os.remove(temp_file_path)
+
+    # Check if the issue is reproduced or resolved
+    try:
+        assert simple_file_permissions == '0o644'
+        assert temp_file_permissions == '0o644'
+        print("Issue resolved")
+    except AssertionError:
+        if simple_file_permissions == '0o644' or temp_file_permissions == '0o600':
+            print("Issue reproduced")
+        else:
+            print("Other issues")
+        return
+
+    return
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

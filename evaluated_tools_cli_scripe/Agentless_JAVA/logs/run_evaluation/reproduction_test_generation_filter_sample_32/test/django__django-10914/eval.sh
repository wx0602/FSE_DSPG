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
@@ -0,0 +1,46 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import TemporaryUploadedFile, MemoryUploadedFile
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions():
+    # Setup
+    storage = FileSystemStorage(location=tempfile.gettempdir())
+
+    # This part simulates the upload of a small file that uses MemoryUploadedFile
+    small_file = MemoryUploadedFile(file=None, field_name='file', name='small.txt', content_type='text/plain', size=10, charset='utf-8')
+    small_file.file = tempfile.SpooledTemporaryFile()
+    small_file.file.write(b"small file")
+    small_file.file.seek(0)
+    small_file._size = small_file.file.size
+
+    # Save small file which should use MemoryUploadedFile
+    small_file_name = storage.save('small.txt', small_file)
+    small_file_path = os.path.join(tempfile.gettempdir(), small_file_name)
+    small_file_permissions = oct(os.stat(small_file_path).st_mode & 0o777)
+
+    # This part simulates the upload of a large file that uses TemporaryUploadedFile
+    large_file = TemporaryUploadedFile(name='large.txt', content_type='text/plain', size=10, charset='utf-8')
+    large_file.file = tempfile.NamedTemporaryFile(delete=False)
+    large_file.file.write(b"large file")
+    large_file.file.seek(0)
+    large_file._size = large_file.file.size
+
+    # Save large file which should use TemporaryUploadedFile
+    large_file_name = storage.save('large.txt', large_file)
+    large_file_path = os.path.join(tempfile.gettempdir(), large_file_name)
+    large_file_permissions = oct(os.stat(large_file_path).st_mode & 0o777)
+
+    # Cleanup
+    os.remove(small_file_path)
+    os.remove(large_file_path)
+
+    # Check permissions
+    if small_file_permissions == '0o644' and large_file_permissions == '0o644':
+        print("Issue resolved")
+    elif small_file_permissions == '0o600' or large_file_permissions == '0o600':
+        print("Issue reproduced")
+    else:
+        print("Other issues")
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

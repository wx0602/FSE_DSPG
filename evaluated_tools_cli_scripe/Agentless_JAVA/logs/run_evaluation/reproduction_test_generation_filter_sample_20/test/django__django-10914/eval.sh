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
@@ -0,0 +1,40 @@
+import os
+import tempfile
+from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
+from django.core.files.storage import FileSystemStorage
+
+def test_file_upload_permissions():
+    # Create a simple uploaded file (small enough to be in-memory)
+    small_file = SimpleUploadedFile("smallfile.txt", b"Test content")
+    storage = FileSystemStorage(location=tempfile.gettempdir())
+    
+    # Save the small file and check its permissions
+    small_file_path = storage.save("smallfile.txt", small_file)
+    small_file_full_path = os.path.join(tempfile.gettempdir(), small_file_path)
+    small_file_permissions = oct(os.stat(small_file_full_path).st_mode & 0o777)
+
+    # Create a temporary uploaded file (large enough to be written to disk)
+    temp_file = TemporaryUploadedFile("largefile.txt", "text/plain", 1048576, "utf-8")
+    temp_file.write(b"Test content" * 1048576)
+    temp_file.seek(0)  # Reset file pointer after write
+    temp_large_file_path = storage.save("largefile.txt", temp_file)
+    temp_large_file_full_path = os.path.join(tempfile.gettempdir(), temp_large_file_path)
+    temp_large_file_permissions = oct(os.stat(temp_large_file_full_path).st_mode & 0o777)
+    
+    try:
+        # Compare permissions
+        if small_file_permissions == "0o644":
+            if temp_large_file_permissions == "0o644":
+                print("Issue resolved")
+            else:
+                print("Issue reproduced")
+        else:
+            print("Other issues")
+    except Exception as e:
+        print(f"Other issues: {e}")
+
+    # Clean up
+    os.remove(small_file_full_path)
+    os.remove(temp_large_file_full_path)
+
+test_file_upload_permissions()

EOF_114329324912
python3 reproduce_bug.py

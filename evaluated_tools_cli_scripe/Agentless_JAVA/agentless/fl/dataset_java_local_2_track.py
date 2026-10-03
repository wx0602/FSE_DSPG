import json
import os

# 函数：生成空的 JSON 数据结构
def generate_empty_json():
    """
    生成一个空的 JSON 数据结构。
    :return: 包含特定键值对的字典形式的 JSON 数据结构
    """
    data = {
        "repo": "",
        "instance_id": "",
        "base_commit": "",
        "environment_setup_commit": "",
        "problem_statement": "",
        "patch": "",
        "test_patch": "",
        "hints_text": "",
        "created_at": "",
        "version": "",
        "FAIL_TO_PASS": [],
        "PASS_TO_PASS": [],
        "local_path" : ""   # 我加的一个新的字段，本地仓库路径
    }
    return data

# 函数：将数据写入 JSONL 文件
def write_jsonl(filename, data_list):
    """
    将数据列表写入到指定的 JSONL 文件中。
    :param filename: 要写入的 JSONL 文件的名称
    :param data_list: 包含 JSON 数据的列表
    """
    with open(filename, 'w') as f:
        for data in data_list:
            try:
                json.dump(data, f)
                f.write('\n')
            except json.JSONEncodeError as e:
                print(f"JSON 编码错误: {e}")


# 函数：读取 JSONL 文件并返回内容
def read_jsonl(filename):
    """
    读取指定的 JSONL 文件并返回其内容。
    :param filename: 要读取的 JSONL 文件的名称
    :return: 包含 JSON 数据的列表，如果文件不存在返回空列表
    """
    data = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                try:
                    data.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    print(f"JSON 解码错误: {e}")
    except FileNotFoundError:
        print(f"文件 {filename} 不存在，返回空列表。")
    return data

# 函数：生成JSON 数据结构
def generate_java_local_json(repo,instance_id,problem_statement,local_path):
    """
    :return: 包含特定键值对的字典形式的 JSON 数据结构
    """
    data = {
        "repo": repo,
        "instance_id": instance_id,
        "base_commit": "",
        "environment_setup_commit": "",
        "problem_statement": problem_statement,
        "patch": "",
        "test_patch": "",
        "hints_text": "",
        "created_at": "",
        "version": "",
        "FAIL_TO_PASS": [],
        "PASS_TO_PASS": [],
        "local_path" : local_path
    }
    return data

def read_md_file(file_path):
    """
    读取指定路径的 md 文件内容
    :param file_path: md 文件路径
    :return: md 文件内容字符串
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"文件 {file_path} 不存在")
        return ""


def generate_json_list(repo_instance_list, md_file_path):
    """
    根据输入的二维列表和 md 文件路径生成 JSON 数据列表
    :param repo_instance_list: 元素是 [repo, instance_id] 的二维列表
    :param md_file_path: md 文件路径
    :return: JSON 数据列表
    """
    problem_statement = read_md_file(md_file_path)
    json_data_list = []
    for sub_list in repo_instance_list:
        repo = sub_list[0]
        instance_id = sub_list[1]
        json_data = generate_java_local_json(repo, instance_id, problem_statement)
        json_data_list.append(json_data)
    return json_data_list

# 主函数：处理本地 JSONL 文件（现不管他）
def process_jsonl_file(input_filename, output_filename):
    """
    处理本地 JSONL 文件，将一个空 JSON 数据结构和另一个 JSONL 文件的内容写入到新的 JSONL 文件中。
    :param input_filename: 输入的 JSONL 文件名称
    :param output_filename: 输出的 JSONL 文件名称
    """
    existing_data = read_jsonl(input_filename)
    new_data = generate_java_local_json()
    all_data = [new_data] + existing_data
    write_jsonl(output_filename, all_data)
    print(f"数据已经成功写入到 {output_filename}")

def main():
    # 从/home/user/AVR_JAVA_STUDY/VESTA_resource/issue/issue19 里读取md文件，md文件文件名通过_分割成两部分，分别是cve编号和项目名，
    #repo是项目名,cve编号_repo是instance_id，problem_statement是从md文件里读取的内容，
    # 从/home/user/AVR_JAVA_STUDY/VESTA_resource/resource/ 里读取对应的项目，如/home/user/AVR_JAVA_STUDY/VESTA_resource/resource/CVE-2021-21341/cqrs-lottery-master，里面是cve编号和项目名，这是local_path字段，我新加的字段
    issue_dir = "/home/user/AVR_JAVA_STUDY/VESTA_resource/issue/63_issues_2_track"
    resource_dir = "/home/user/AVR_JAVA_STUDY/VESTA_resource/resource/"
    output_jsonl_file = "/home/user/AVR_JAVA_STUDY/agentless/Agentless/agentless/fl/local_java_dataset/poc_bench.jsonl"
    json_data_list = []
    md_number=0
    for filename in os.listdir(issue_dir):
        if filename.endswith(".md"):
            parts = filename.split('_',1)
            if len(parts) == 2:
                cve_id = parts[0]
                repo = parts[1].split('.')[0]
                md_file_path = os.path.join(issue_dir, filename)
                problem_statement = read_md_file(md_file_path)
                local_path = os.path.join(resource_dir, cve_id, repo)
                print(cve_id.ljust(20),repo)
                md_number+=1
                if os.path.exists(local_path):
                    json_data = generate_java_local_json(repo, cve_id+"_"+repo, problem_statement, local_path)
                    json_data_list.append(json_data)
                else:
                    print(f"路径 {local_path} 不存在,没有这个local代码仓库")
            else:
                print(f"文件名 {filename} 不符合预期格式，可能是制作issue没有使用下划线")
    print(f"一共处理的md文件数量{md_number}")
    write_jsonl(output_jsonl_file, json_data_list)

if __name__ == "__main__":
    main()




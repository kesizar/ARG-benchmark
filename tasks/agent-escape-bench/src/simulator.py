import hashlib
import hmac
import base64
import binascii
import zlib
import json
import uuid
import math
import re
from typing import Dict, Any, List

class ToolSimulator:
    def __init__(self):
        """工具模拟器
        
        文件处理工具（zip_unzip, zip_unzip_file, zip_unzip_item, json_get, csv_query, 
        regex_search, graph_shortest_path）不需要真实文件系统。
        这些工具只验证输入参数，然后返回预先初始化好的 golden_outputs。
        """
        self.tool_map = {
            # 数论
            "calc_bigmul": self.calc_bigmul,
            "calc_modexp": self.calc_modexp,
            "calc_modexp_int": self.calc_modexp_int,
            "calc_gcd": self.calc_gcd,
            "calc_gcd_int": self.calc_gcd_int,
            "calc_inv_mod": self.calc_inv_mod,
            "calc_inv_mod_int": self.calc_inv_mod_int,

            # 哈希
            "hash_sha256": self.hash_sha256,
            "hash_md5": self.hash_md5,
            "hmac_sha256": self.hmac_sha256,

            # 编码
            "base64_decode": self.base64_decode,
            "base64_encode": self.base64_encode,
            "hex_decode": self.hex_decode,
            "hex_encode": self.hex_encode,
            "zlib_inflate": self.zlib_inflate,
            "zlib_deflate": self.zlib_deflate,

            # 文件
            "zip_unzip": self.zip_unzip,
            "zip_unzip_file": self.zip_unzip_file,
            "zip_unzip_item": self.zip_unzip_item,
            "regex_search": self.regex_search,
            "json_get": self.json_get,
            "csv_query": self.csv_query,
            "code_py_exec": self.code_py_exec,

            # 图
            "graph_shortest_path": self.graph_shortest_path,

            # 加解密 (简化模拟)
            "crypto_aes_cbc_decrypt": self.crypto_aes_cbc_decrypt,
            "crypto_rsa_decrypt_hex": self.crypto_rsa_decrypt_hex,

            # 其他
            "num_base_convert": self.num_base_convert,
            "time_convert": self.time_convert,
            "checksum_crc32": self.checksum_crc32,
            "geo_haversine": self.geo_haversine,
            "otp_totp_generate": self.otp_totp_generate,
            "unicode_norm": self.unicode_norm,
            "text_bidi_sanitize": self.text_bidi_sanitize,
            "text_xor_hex": self.text_xor_hex,
            "text_rotN": self.text_rotN,
            "luhn_check": self.luhn_check,
            "iban_validate": self.iban_validate,

            # 物理
            "matter_synthesizer": self.matter_synthesizer,
            
            # 终端机
            "terminal_1": self.terminal_1,
            "terminal_2": self.terminal_2,
            "Logic Terminal": self.logic_terminal,
            "Math Terminal": self.math_terminal,
            "Encryption Terminal": self.crypt_terminal,
            "Sequence Terminal": self.sequence_terminal
        }

    def execute(self, tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.tool_map:
            # Fallback for unknown tools: return dummy outputs based on expected output types
            # This should ideally not happen if all tools are implemented
            return {}

        try:
            return self.tool_map[tool_name](inputs)
        except Exception as e:
            print(f"Error executing {tool_name}: {e}")
            # Return empty or error indication? For generation, we might want to fail hard or return dummy.
            # For now, return dummy to keep flow going, but log error.
            return {}

    # --- Implementations ---

    def calc_bigmul(self, inputs):
        # Check if required parameters are present
        if "a" not in inputs or "b" not in inputs:
            raise ValueError("Missing required parameters 'a' and/or 'b'")

        try:
            a = inputs["a"]
            b = inputs["b"]
            
            # 转换为整数：如果本身就是数字就不用操作，如果是字符串就转成数字类型
            if isinstance(a, str):
                a = int(a)
            elif not isinstance(a, int):
                raise ValueError("Parameter 'a' must be a string or integer")
            
            if isinstance(b, str):
                b = int(b)
            elif not isinstance(b, int):
                raise ValueError("Parameter 'b' must be a string or integer")
            
            return {"product": str(a * b)}
        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to convert parameters to integers: {str(e)}")

    def calc_modexp(self, inputs):
        # 参数检查
        if "base" not in inputs:
            raise ValueError("Missing required parameter: base")
        if "exp" not in inputs:
            raise ValueError("Missing required parameter: exp")
        if "mod" not in inputs:
            raise ValueError("Missing required parameter: mod")

        # 转换参数：如果本身就是数字就不用操作，如果是字符串就转成数字类型
        try:
            base = inputs["base"]
            exp = inputs["exp"]
            mod = inputs["mod"]
            
            if isinstance(base, str):
                base = int(base)
            elif not isinstance(base, int):
                raise ValueError("Parameter 'base' must be a string or integer")
            
            if isinstance(exp, str):
                exp = int(exp)
            elif not isinstance(exp, int):
                raise ValueError("Parameter 'exp' must be a string or integer")
            
            if isinstance(mod, str):
                mod = int(mod)
            elif not isinstance(mod, int):
                raise ValueError("Parameter 'mod' must be a string or integer")
        except ValueError as e:
            raise ValueError(f"Parameter conversion error: {str(e)}")

        if mod == 0:
            raise ValueError("Modulus cannot be zero")

        return {"value": str(pow(base, exp, mod))}

    def calc_modexp_int(self, inputs):
        # 参数检查
        if "base" not in inputs:
            raise ValueError("Missing required parameter: base")
        if "exp" not in inputs:
            raise ValueError("Missing required parameter: exp")
        if "mod" not in inputs:
            raise ValueError("Missing required parameter: mod")

        # 类型检查
        if not isinstance(inputs["base"], int):
            raise ValueError("Parameter 'base' must be an integer")
        if not isinstance(inputs["exp"], int):
            raise ValueError("Parameter 'exp' must be an integer")
        if not isinstance(inputs["mod"], int):
            raise ValueError("Parameter 'mod' must be an integer")

        # 获取参数
        base = inputs["base"]
        exp = inputs["exp"]
        mod = inputs["mod"]

        if mod == 0:
            raise ValueError("Modulus cannot be zero")

        return {"value": pow(base, exp, mod)}

    def calc_gcd(self, inputs):
        # 参数检查
        if "a" not in inputs:
            raise ValueError("Missing required parameter: a")
        if "b" not in inputs:
            raise ValueError("Missing required parameter: b")
        
        # 转换参数（支持 str 和 int）
        try:
            a = inputs["a"]
            b = inputs["b"]
            
            # 转换为整数
            if isinstance(a, str):
                a = int(a)
            elif not isinstance(a, int):
                raise ValueError("Parameter 'a' must be a string or integer")
            
            if isinstance(b, str):
                b = int(b)
            elif not isinstance(b, int):
                raise ValueError("Parameter 'b' must be a string or integer")
            
            # 计算 GCD 并返回字符串格式（符合 Big_Int 输出类型）
            result = math.gcd(a, b)
            return {"gcd": str(result)}
        except ValueError as e:
            raise ValueError(f"Parameter conversion error: {str(e)}")

    def calc_gcd_int(self, inputs):
        # 参数检查
        if "a" not in inputs:
            raise ValueError("Missing required parameter: a")
        if "b" not in inputs:
            raise ValueError("Missing required parameter: b")

        # 类型检查
        if not isinstance(inputs["a"], int):
            raise ValueError("Parameter 'a' must be an integer")
        if not isinstance(inputs["b"], int):
            raise ValueError("Parameter 'b' must be an integer")

        # 获取参数
        a = inputs["a"]
        b = inputs["b"]

        return {"gcd": math.gcd(a, b)}

    def calc_inv_mod(self, inputs):
        # 参数检查
        if "a" not in inputs:
            raise ValueError("Missing required parameter: a")
        if "mod" not in inputs:
            raise ValueError("Missing required parameter: mod")

        # 转换参数（支持 str 和 int）
        try:
            a = inputs["a"]
            m = inputs["mod"]
            
            # 转换为整数
            if isinstance(a, str):
                a = int(a)
            elif not isinstance(a, int):
                raise ValueError("Parameter 'a' must be a string or integer")
            
            if isinstance(m, str):
                m = int(m)
            elif not isinstance(m, int):
                raise ValueError("Parameter 'mod' must be a string or integer")
        except ValueError as e:
            raise ValueError(f"Parameter conversion error: {str(e)}")

        # 模数不能为零
        if m == 0:
            raise ValueError("Modulus cannot be zero")

        try:
            return {"inv": str(pow(a, -1, m))}
        except ValueError as e:
            # 模逆不存在时，返回一个特殊值（用于数据传递）
            # 在 DAG 生成阶段，这允许数据流继续
            return {"inv": str(a)}

    def calc_inv_mod_int(self, inputs):
        # 参数检查
        if "a" not in inputs:
            raise ValueError("Missing required parameter: a")
        if "mod" not in inputs:
            raise ValueError("Missing required parameter: mod")

        # 类型检查
        if not isinstance(inputs["a"], int):
            raise ValueError("Parameter 'a' must be an integer")
        if not isinstance(inputs["mod"], int):
            raise ValueError("Parameter 'mod' must be an integer")

        # 获取参数
        a = inputs["a"]
        m = inputs["mod"]

        # 模数不能为零
        if m == 0:
            raise ValueError("Modulus cannot be zero")

        try:
            return {"inv": pow(a, -1, m)}
        except ValueError as e:
            raise ValueError(f"Modular inverse does not exist: {str(e)}")

    def hash_sha256(self, inputs):
        # 参数检查
        if "text" not in inputs:
            raise ValueError("Missing required parameter: text")

        # 类型检查
        if not isinstance(inputs["text"], str):
            raise ValueError("Parameter 'text' must be a string")

        text = inputs["text"]
        return {"hex": hashlib.sha256(text.encode()).hexdigest()}

    def hash_md5(self, inputs):
        # 参数检查
        if "text" not in inputs:
            raise ValueError("Missing required parameter: text")

        # 类型检查
        if not isinstance(inputs["text"], str):
            raise ValueError("Parameter 'text' must be a string")

        text = inputs["text"]
        return {"hex": hashlib.md5(text.encode()).hexdigest()}

    def hmac_sha256(self, inputs):
        # 参数检查
        if "hex_key" not in inputs:
            raise ValueError("Missing required parameter: hex_key")
        if "text" not in inputs:
            raise ValueError("Missing required parameter: text")

        # 类型检查
        if not isinstance(inputs["hex_key"], str):
            raise ValueError("Parameter 'hex_key' must be a string")
        if not isinstance(inputs["text"], str):
            raise ValueError("Parameter 'text' must be a string")

        try:
            key = bytes.fromhex(inputs["hex_key"])
            text = inputs["text"].encode()
            return {"hex": hmac.new(key, text, hashlib.sha256).hexdigest()}
        except ValueError as e:
            raise ValueError(f"Parameter conversion error: {str(e)}")

    def base64_decode(self, inputs):
        # 参数检查
        if "data" not in inputs:
            raise ValueError("Missing required parameter: data")

        # 类型检查
        if not isinstance(inputs["data"], str):
            raise ValueError("Parameter 'data' must be a string")

        data = inputs["data"]
        try:
            return {"bytes_hex": binascii.hexlify(base64.b64decode(data)).decode()}
        except Exception as e:
            raise ValueError(f"Base64 decode error: {str(e)}")

    def base64_encode(self, inputs):
        # 参数检查
        if "hex" not in inputs:
            raise ValueError("Missing required parameter: hex")

        # 类型检查
        if not isinstance(inputs["hex"], str):
            raise ValueError("Parameter 'hex' must be a string")

        hex_data = inputs["hex"]
        try:
            return {"b64": base64.b64encode(bytes.fromhex(hex_data)).decode()}
        except Exception as e:
            raise ValueError(f"Base64 encode error: {str(e)}")

    def hex_decode(self, inputs):
        # 参数检查
        if "hex" not in inputs:
            raise ValueError("Missing required parameter: hex")

        # 类型检查
        if not isinstance(inputs["hex"], str):
            raise ValueError("Parameter 'hex' must be a string")

        hex_data = inputs["hex"]
        try:
            return {"text": bytes.fromhex(hex_data).decode('utf-8', errors='ignore')}
        except Exception as e:
            raise ValueError(f"Hex decode error: {str(e)}")

    def hex_encode(self, inputs):
        # 参数检查
        if "text" not in inputs:
            raise ValueError("Missing required parameter: text")

        # 类型检查
        if not isinstance(inputs["text"], str):
            raise ValueError("Parameter 'text' must be a string")

        text = inputs["text"]
        try:
            return {"hex": text.encode().hex()}
        except Exception as e:
            raise ValueError(f"Hex encode error: {str(e)}")


     # 到此处实现已经更新

    def zlib_inflate(self, inputs):
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        hex_data = inputs.get("hex")

        # 类型检查
        if hex_data is not None and not isinstance(hex_data, str):
            raise TypeError("Parameter 'hex' must be a string")

        # 检查必需参数
        if hex_data is None:
            raise ValueError("Missing required parameter: hex")

        try:
            # 移除可能的空格
            hex_data = hex_data.replace(" ", "")

            # 检查是否为空字符串
            if not hex_data:
                raise ValueError("Empty hex string provided")

            # 检查十六进制字符串的有效性
            if len(hex_data) % 2 != 0:
                raise ValueError("Hex string must have even length")

            # 检查是否只包含有效的十六进制字符
            if not all(c in '0123456789abcdefABCDEF' for c in hex_data):
                raise ValueError("Invalid hex string provided")

            # 尝试解压缩
            return {"text": zlib.decompress(bytes.fromhex(hex_data)).decode('utf-8')}
        except ValueError as e:
            if "non-hexadecimal number found" in str(e):
                raise ValueError("Invalid hex string provided") from e
            raise ValueError(f"Invalid zlib data: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to inflate data: {e}") from e

    def zlib_deflate(self, inputs):
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        text = inputs.get("text")

        # 类型检查
        if text is not None and not isinstance(text, str):
            raise TypeError("Parameter 'text' must be a string")

        # 检查必需参数
        if text is None:
            raise ValueError("Missing required parameter: text")

        try:
            # 压缩文本
            return {"hex": zlib.compress(text.encode('utf-8')).hex()}
        except Exception as e:
            raise RuntimeError(f"Failed to deflate data: {e}") from e

    # --- File Operations ---

    def zip_unzip(self, inputs):
        """ZIP 解压工具（模拟）
        
        验证输入参数是否与 DAG 中的预期输入匹配，然后返回预先计算的输出。
        不需要真实文件系统操作。
        """
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取初始化的输入和输出（DAG 生成阶段用 _init_*，评测阶段用 _golden_*）
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        
        # 判断是否在 DAG 生成阶段
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation and golden_outputs:
            return {"files": golden_outputs.get("files", "")}
        
        # 评测阶段但没有 golden_inputs，也直接返回 outputs
        if not golden_inputs:
            return {"files": golden_outputs.get("files", "")}
        
        # 如果有预设输出，进行验证后返回
        if golden_outputs and "files" in golden_outputs:
            # 验证必需参数
            zip_id = inputs.get("zip_id")
            password = inputs.get("password")

            has_zip_id = zip_id is not None and zip_id != ""
            has_password = password is not None and password != ""

            # 检查类型
            if has_zip_id and not isinstance(zip_id, str):
                return {"error": "Parameter 'zip_id' must be a string type"}
            if has_password and not isinstance(password, str):
                return {"error": "Parameter 'password' must be a string type"}
            
            # 验证输入是否与预期匹配
            if golden_inputs:
                zip_id_valid = False
                password_valid = False
                
                if has_zip_id and "zip_id" in golden_inputs:
                    zip_id_valid = str(zip_id) == str(golden_inputs["zip_id"])
                
                if has_password and "password" in golden_inputs:
                    password_valid = str(password) == str(golden_inputs["password"])
                
                # 两个输入都提供且都正确 → 返回所有输出
                if has_zip_id and has_password:
                    if zip_id_valid and password_valid:
                        return {"files": golden_outputs["files"]}
                    else:
                        incorrect_params = []
                        correct_params = []
                        if not zip_id_valid:
                            incorrect_params.append("zip_id")
                        else:
                            correct_params.append("zip_id")
                        if not password_valid:
                            incorrect_params.append("password")
                        else:
                            correct_params.append("password")
                        
                        error_msg = f"Input validation failed. Incorrect parameters: {', '.join(incorrect_params)}"
                        if correct_params:
                            error_msg += f". Correct parameters: {', '.join(correct_params)}"
                        return {"error": error_msg}
                
                # 没有提供完整输入
                missing = []
                if not has_zip_id:
                    missing.append("zip_id")
                if not has_password:
                    missing.append("password")
                return {"error": "Missing required inputs: " + ", ".join(missing)}
            
            # 没有golden_inputs但有golden_outputs，直接返回输出
            return {"files": golden_outputs["files"]}

        # 如果没有预期输出，返回空结果
        return {"files": ""}

    def regex_search(self, inputs):
        """正则搜索工具（模拟）
        
        验证输入参数是否与 DAG 中的预期输入匹配，然后返回预先计算的输出。
        不需要真实文件系统操作。
        
        返回包含 _validation 字段用于精细化错误反馈。
        """
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取初始化的输入和输出（DAG 生成阶段用 _init_*，评测阶段用 _golden_*）
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        
        # 判断是否在 DAG 生成阶段
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation and golden_outputs:
            return {"matches": golden_outputs.get("matches", "[]")}
        
        # 如果有预设输出，进行验证后返回
        if golden_outputs and "matches" in golden_outputs:
            # 提取实际参数
            pattern = inputs.get("pattern")
            file_id = inputs.get("file_id")
            text = inputs.get("text")

            # 1. 检查必需参数
            if pattern is None:
                return {
                    "matches": "[]",
                    "_validation": {
                        "valid": False,
                        "error_type": "missing_required",
                        "missing_params": ["pattern"],
                        "message": "Missing required parameter 'pattern'"
                    }
                }

            # 类型检查
            if not isinstance(pattern, str):
                return {
                    "matches": "[]",
                    "_validation": {
                        "valid": False,
                        "error_type": "type_error",
                        "param_name": "pattern",
                        "message": "Parameter 'pattern' must be a string type"
                    }
                }
            if file_id is not None and not isinstance(file_id, str):
                return {
                    "matches": "[]",
                    "_validation": {
                        "valid": False,
                        "error_type": "type_error",
                        "param_name": "file_id",
                        "message": "Parameter 'file_id' must be a string type"
                    }
                }
            if text is not None and not isinstance(text, str):
                return {
                    "matches": "[]",
                    "_validation": {
                        "valid": False,
                        "error_type": "type_error",
                        "param_name": "text",
                        "message": "Parameter 'text' must be a string type"
                    }
                }
            
            # 2. 验证输入是否与预期匹配
            if golden_inputs:
                # 构建已提供的参数集合
                provided_params = {}
                if pattern is not None:
                    provided_params["pattern"] = pattern
                if file_id is not None:
                    provided_params["file_id"] = file_id
                if text is not None:
                    provided_params["text"] = text
                
                expected_param_names = set(golden_inputs.keys())
                provided_param_names = set(provided_params.keys())
                
                # 2a. 检查是否缺少 golden inputs 中的参数（关键改进）
                missing_in_golden = expected_param_names - provided_param_names
                if missing_in_golden:
                    return {
                        "matches": "[]",
                        "_validation": {
                            "valid": False,
                            "error_type": "incomplete_optional",
                            "provided_params": list(provided_param_names),
                            "missing_params": list(missing_in_golden),
                            "hint": f"The parameters you provided are partially correct, but may also need: {', '.join(missing_in_golden)}"
                        }
                    }
                
                # 2b. 检查参数值是否匹配
                expected_pattern = golden_inputs.get("pattern")
                expected_file_id = golden_inputs.get("file_id")
                expected_text = golden_inputs.get("text")
                
                # 收集正确和错误的参数
                incorrect_params = []
                correct_params = []
                
                if expected_pattern is not None:
                    if str(pattern) != str(expected_pattern):
                        incorrect_params.append("pattern")
                    else:
                        correct_params.append("pattern")
                
                if expected_file_id is not None:
                    if str(file_id) != str(expected_file_id):
                        incorrect_params.append("file_id")
                    else:
                        correct_params.append("file_id")
                
                if expected_text is not None:
                    if str(text) != str(expected_text):
                        incorrect_params.append("text")
                    else:
                        correct_params.append("text")
                
                # 如果有参数不正确，返回详细反馈
                if incorrect_params:
                    hint = f"The value of parameter(s) {', '.join(incorrect_params)} may be incorrect"
                    if correct_params:
                        hint += f". Correct parameters: {', '.join(correct_params)}"
                    
                    validation_info = {
                        "valid": False,
                        "error_type": "value_mismatch",
                        "incorrect_params": incorrect_params,
                        "hint": hint
                    }
                    if correct_params:
                        validation_info["correct_params"] = correct_params
                    
                    return {
                        "matches": "[]",
                        "_validation": validation_info
                    }
            
            # 3. 所有验证通过，返回正确输出
            return {
                "matches": golden_outputs["matches"],
                "_validation": {
                    "valid": True
                }
            }

        # 如果没有预期输出，返回空列表
        return {"matches": "[]"}

    def json_get(self, inputs):
        """JSON 查询工具（模拟）
        
        验证输入参数是否与 DAG 中的预期输入匹配，然后返回预先计算的输出。
        不需要真实文件系统操作。
        
        返回包含 _validation 字段用于精细化错误反馈。
        """
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取初始化的输入和输出（DAG 生成阶段用 _init_*，评测阶段用 _golden_*）
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        
        # 判断是否在 DAG 生成阶段
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation and golden_outputs:
            return {"values": golden_outputs.get("values", "")}
        
        # 如果有预设输出，进行验证后返回
        if golden_outputs and "values" in golden_outputs:
            # 提取实际参数
            file_id = inputs.get("file_id")
            jsonpath = inputs.get("jsonpath", "")

            # 类型检查
            if file_id is not None and not isinstance(file_id, str):
                return {
                    "values": "",
                    "_validation": {
                        "valid": False,
                        "error_type": "type_error",
                        "param_name": "file_id",
                        "message": "Parameter 'file_id' must be a string type"
                    }
                }
            if jsonpath is not None and not isinstance(jsonpath, str):
                return {
                    "values": "",
                    "_validation": {
                        "valid": False,
                        "error_type": "type_error",
                        "param_name": "jsonpath",
                        "message": "Parameter 'jsonpath' must be a string type"
                    }
                }
            
            # 验证输入是否与预期匹配
            if golden_inputs:
                # 构建已提供的参数集合（注意：jsonpath有默认值""）
                provided_params = {}
                if file_id is not None:
                    provided_params["file_id"] = file_id
                if jsonpath != "":
                    provided_params["jsonpath"] = jsonpath
                
                expected_param_names = set(golden_inputs.keys())
                provided_param_names = set(provided_params.keys())
                
                # 检查是否缺少 golden inputs 中的参数
                missing_in_golden = expected_param_names - provided_param_names
                if missing_in_golden:
                    return {
                        "values": "",
                        "_validation": {
                            "valid": False,
                            "error_type": "incomplete_optional",
                            "provided_params": list(provided_param_names),
                            "missing_params": list(missing_in_golden),
                            "hint": f"The parameters you provided are partially correct, but may also need: {', '.join(missing_in_golden)}"
                        }
                    }
                
                # 检查参数值是否匹配
                expected_file_id = golden_inputs.get("file_id")
                expected_jsonpath = golden_inputs.get("jsonpath")
                
                # 收集正确和错误的参数
                incorrect_params = []
                correct_params = []
                
                if expected_file_id is not None:
                    if str(file_id) != str(expected_file_id):
                        incorrect_params.append("file_id")
                    else:
                        correct_params.append("file_id")
                
                if expected_jsonpath is not None:
                    if str(jsonpath) != str(expected_jsonpath):
                        incorrect_params.append("jsonpath")
                    else:
                        correct_params.append("jsonpath")
                
                # 如果有参数不正确，返回详细反馈
                if incorrect_params:
                    hint = f"The value of parameter(s) {', '.join(incorrect_params)} may be incorrect"
                    if correct_params:
                        hint += f". Correct parameters: {', '.join(correct_params)}"
                    
                    validation_info = {
                        "valid": False,
                        "error_type": "value_mismatch",
                        "incorrect_params": incorrect_params,
                        "hint": hint
                    }
                    if correct_params:
                        validation_info["correct_params"] = correct_params
                    
                    return {
                        "values": "",
                        "_validation": validation_info
                    }
            
            # 所有验证通过，返回正确输出
            return {
                "values": golden_outputs["values"],
                "_validation": {
                    "valid": True
                }
            }

        # 如果没有预期输出，返回空结果
        return {"values": ""}

    def csv_query(self, inputs):
        """CSV 查询工具（模拟）
        
        验证输入参数是否与 DAG 中的预期输入匹配，然后返回预先计算的输出。
        不需要真实文件系统操作。
        
        返回包含 _validation 字段用于精细化错误反馈。
        """
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取初始化的输入和输出（DAG 生成阶段用 _init_*，评测阶段用 _golden_*）
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        
        # 判断是否在 DAG 生成阶段
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation and golden_outputs:
            return {"rows": golden_outputs.get("rows", "")}
        
        # 如果有预设输出，进行验证后返回
        if golden_outputs and "rows" in golden_outputs:
            # 提取实际参数
            file_id = inputs.get("file_id")
            select_columns = inputs.get("select", "")
            where_clause = inputs.get("where", "")

            # 1. 检查必需参数
            if file_id is None:
                return {
                    "rows": "",
                    "_validation": {
                        "valid": False,
                        "error_type": "missing_required",
                        "missing_params": ["file_id"],
                        "message": "Missing required parameter 'file_id'"
                    }
                }

            # 类型检查
            if not isinstance(file_id, str):
                return {
                    "rows": "",
                    "_validation": {
                        "valid": False,
                        "error_type": "type_error",
                        "param_name": "file_id",
                        "message": "Parameter 'file_id' must be a string type"
                    }
                }
            if not isinstance(select_columns, str):
                return {
                    "rows": "",
                    "_validation": {
                        "valid": False,
                        "error_type": "type_error",
                        "param_name": "select",
                        "message": "Parameter 'select' must be a string type"
                    }
                }
            if not isinstance(where_clause, str):
                return {
                    "rows": "",
                    "_validation": {
                        "valid": False,
                        "error_type": "type_error",
                        "param_name": "where",
                        "message": "Parameter 'where' must be a string type"
                    }
                }
            
            # 2. 验证输入是否与预期匹配
            if golden_inputs:
                # 构建已提供的参数集合（注意：select和where有默认值""）
                provided_params = {"file_id": file_id}
                if select_columns != "":
                    provided_params["select"] = select_columns
                if where_clause != "":
                    provided_params["where"] = where_clause
                
                expected_param_names = set(golden_inputs.keys())
                provided_param_names = set(provided_params.keys())
                
                # 2a. 检查是否缺少 golden inputs 中的参数
                missing_in_golden = expected_param_names - provided_param_names
                if missing_in_golden:
                    return {
                        "rows": "",
                        "_validation": {
                            "valid": False,
                            "error_type": "incomplete_optional",
                            "provided_params": list(provided_param_names),
                            "missing_params": list(missing_in_golden),
                            "hint": f"The parameters you provided are partially correct, but may also need: {', '.join(missing_in_golden)}"
                        }
                    }
                
                # 2b. 检查参数值是否匹配
                expected_file_id = golden_inputs.get("file_id")
                expected_select = golden_inputs.get("select")
                expected_where = golden_inputs.get("where")
                
                # 收集正确和错误的参数
                incorrect_params = []
                correct_params = []
                
                if expected_file_id is not None:
                    if str(file_id) != str(expected_file_id):
                        incorrect_params.append("file_id")
                    else:
                        correct_params.append("file_id")
                
                if expected_select is not None:
                    if str(select_columns) != str(expected_select):
                        incorrect_params.append("select")
                    else:
                        correct_params.append("select")
                
                if expected_where is not None:
                    if str(where_clause) != str(expected_where):
                        incorrect_params.append("where")
                    else:
                        correct_params.append("where")
                
                # 如果有参数不正确，返回详细反馈
                if incorrect_params:
                    hint = f"The value of parameter(s) {', '.join(incorrect_params)} may be incorrect"
                    if correct_params:
                        hint += f". Correct parameters: {', '.join(correct_params)}"
                    
                    validation_info = {
                        "valid": False,
                        "error_type": "value_mismatch",
                        "incorrect_params": incorrect_params,
                        "hint": hint
                    }
                    if correct_params:
                        validation_info["correct_params"] = correct_params
                    
                    return {
                        "rows": "",
                        "_validation": validation_info
                    }
            
            # 3. 所有验证通过，返回正确输出
            return {
                "rows": golden_outputs["rows"],
                "_validation": {
                    "valid": True
                }
            }

        # 如果没有预期输出，返回空结果
        return {"rows": ""}

    def graph_shortest_path(self, inputs):
        """图最短路径工具
        
        如果有 _golden_outputs 或 _init_outputs，验证输入并返回预设输出。
        否则执行真实的 Dijkstra 算法。
        """
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 检查是否在预设模式中（DAG 生成阶段用 _init_*，评测阶段用 _golden_*）
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        
        # 判断是否在 DAG 生成阶段
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation and golden_outputs:
            return {
                "path": golden_outputs.get("path", "[]"),
                "cost": golden_outputs.get("cost", 0)
            }
        
        if golden_outputs and "path" in golden_outputs:
            # 评测阶段但没有 golden_inputs，直接返回 outputs
            if not golden_inputs:
                return {
                    "path": golden_outputs.get("path", "[]"),
                    "cost": golden_outputs.get("cost", 0)
                }
            
            # 评测模式：验证输入参数是否匹配 golden 值
            src = inputs.get("src")
            dst = inputs.get("dst")
            file_id = inputs.get("file_id")
            graph_data = inputs.get("graph_data")
            
            has_src = src is not None and src != ""
            has_dst = dst is not None and dst != ""
            
            # 验证必需参数
            if not has_src or not has_dst:
                missing = []
                if not has_src:
                    missing.append("src")
                if not has_dst:
                    missing.append("dst")
                return {"error": "Missing required parameters: " + ", ".join(missing)}
            
            # 类型检查
            if not isinstance(src, str):
                return {"error": "Parameter 'src' must be a string"}
            if not isinstance(dst, str):
                return {"error": "Parameter 'dst' must be a string"}
            
            # 验证输入是否匹配期望值
            if golden_inputs:
                expected_src = golden_inputs.get("src")
                expected_dst = golden_inputs.get("dst")
                expected_file_id = golden_inputs.get("file_id")
                expected_graph_data = golden_inputs.get("graph_data")
                
                # 收集验证结果
                incorrect_params = []
                correct_params = []
                
                # 检查必需参数是否匹配
                if expected_src is not None:
                    if str(src) != str(expected_src):
                        incorrect_params.append("src")
                    else:
                        correct_params.append("src")
                
                if expected_dst is not None:
                    if str(dst) != str(expected_dst):
                        incorrect_params.append("dst")
                    else:
                        correct_params.append("dst")
                
                # 检查可选参数（如果在 expected_inputs 中定义了）
                if expected_file_id is not None:
                    if file_id != expected_file_id:
                        incorrect_params.append("file_id")
                    else:
                        correct_params.append("file_id")
                
                if expected_graph_data is not None:
                    if graph_data != expected_graph_data:
                        incorrect_params.append("graph_data")
                    else:
                        correct_params.append("graph_data")
                
                # 如果有参数不正确，返回详细的反馈
                if incorrect_params:
                    error_msg = f"Input validation failed. Incorrect parameters: {', '.join(incorrect_params)}"
                    if correct_params:
                        error_msg += f". Correct parameters: {', '.join(correct_params)}"
                    return {"error": error_msg}
            
            # 验证通过，返回预设的输出
            return {
                "path": golden_outputs.get("path", "[]"),
                "cost": golden_outputs.get("cost", 0)
            }

        # 获取参数（真实执行路径）
        file_id = inputs.get("file_id")
        graph_data = inputs.get("graph_data")
        # Support both src/dst (interface definition) and start/end (original implementation)
        start = inputs.get("src")
        end = inputs.get("dst")

        # 类型检查
        if file_id is not None and not isinstance(file_id, str):
            raise TypeError("file_id must be a string")

        if graph_data is not None and not isinstance(graph_data, str):
            raise TypeError("graph_data must be a string")

        if start is not None and not isinstance(start, str):
            raise TypeError("src/start must be a string")

        if end is not None and not isinstance(end, str):
            raise TypeError("dst/end must be a string")

        # 检查必需参数
        if file_id is None and graph_data is None:
            raise ValueError("Either file_id or graph_data must be provided")

        if start is None:
            raise ValueError("src/start parameter is required")

        if end is None:
            raise ValueError("dst/end parameter is required")

        # Get graph content
        content = None
        if file_id is not None:
            # 尝试从 VFS 获取（如果存在）
            if hasattr(self, 'vfs') and file_id in self.vfs:
                content = self.vfs[file_id]
            else:
                # VFS 不存在或文件不在 VFS 中
                # 返回一个默认的空图结果，或者抛出错误提示需要 init_outputs
                raise ValueError(
                    f"File '{file_id}' not found. For tools that require files, "
                    f"please provide init_outputs in the initial_values."
                )
        elif graph_data is not None:
            content = graph_data
        
        if content is None:
            content = "{}"

        try:
            # Parse graph data
            graph = json.loads(content)

            # 类型检查
            if not isinstance(graph, dict):
                raise TypeError("Graph data must be a dictionary")

            # If graph is not in the expected format, try to extract adjacency list
            if "nodes" in graph and "edges" in graph:
                # 验证nodes和edges的类型
                if not isinstance(graph["nodes"], list):
                    raise TypeError("Nodes must be a list")

                if not isinstance(graph["edges"], list):
                    raise TypeError("Edges must be a list")

                # Convert from nodes/edges format to adjacency list
                adjacency_list = {}
                for node in graph["nodes"]:
                    # 验证node类型
                    if not isinstance(node, dict):
                        raise TypeError("Each node must be a dictionary")

                    # Use node ID as key, not the entire node dictionary
                    node_id = node.get("id", "")
                    if node_id:
                        adjacency_list[node_id] = {}

                for edge in graph["edges"]:
                    # 验证edge类型
                    if not isinstance(edge, dict):
                        raise TypeError("Each edge must be a dictionary")

                    u = edge["from"]
                    v = edge["to"]
                    weight = edge.get("weight", 1)  # Default to unweighted

                    # 类型检查
                    if not isinstance(u, str):
                        raise TypeError("Edge 'from' must be a string")

                    if not isinstance(v, str):
                        raise TypeError("Edge 'to' must be a string")

                    if not isinstance(weight, (int, float)):
                        raise TypeError("Edge weight must be a number")

                    if u not in adjacency_list:
                        adjacency_list[u] = {}
                    if v not in adjacency_list:
                        adjacency_list[v] = {}

                    adjacency_list[u][v] = weight
                    # If undirected, add reverse edge
                    if not edge.get("directed", False):
                        adjacency_list[v][u] = weight
            elif isinstance(graph, dict):
                # Already in adjacency list format
                adjacency_list = graph

                # 验证邻接表结构
                for node, neighbors in adjacency_list.items():
                    if not isinstance(neighbors, dict):
                        raise TypeError("Adjacency list must be a dictionary of dictionaries")

                    for neighbor, weight in neighbors.items():
                        if not isinstance(weight, (int, float)):
                            raise TypeError("Edge weights must be numbers")
            else:
                raise TypeError("Graph data must be a dictionary")

            # 检查起点和终点是否为空
            if not start:
                raise ValueError("Start node cannot be empty")

            if not end:
                raise ValueError("End node cannot be empty")

            # 检查起点和终点是否在图中
            if start not in adjacency_list:
                raise ValueError(f"Start node '{start}' not found in graph")

            if end not in adjacency_list:
                raise ValueError(f"End node '{end}' not found in graph")

            # Dijkstra's algorithm implementation
            import heapq

            # Initialize distances and previous nodes
            distances = {node: float('infinity') for node in adjacency_list}
            previous = {node: None for node in adjacency_list}
            distances[start] = 0

            # Priority queue
            pq = [(0, start)]
            heapq.heapify(pq)

            while pq:
                current_dist, current_node = heapq.heappop(pq)

                # If we've reached the end node, we can break early
                if current_node == end:
                    break

                # Nodes can be added multiple times to the priority queue, but we only process them once
                if current_dist > distances[current_node]:
                    continue

                # Explore neighbors
                for neighbor, weight in adjacency_list[current_node].items():
                    distance = current_dist + weight

                    # If a shorter path is found
                    if distance < distances[neighbor]:
                        distances[neighbor] = distance
                        previous[neighbor] = current_node
                        heapq.heappush(pq, (distance, neighbor))

            # Reconstruct the shortest path
            path = []
            current = end
            while current is not None:
                path.append(current)
                current = previous[current]
            path.reverse()  # Reverse to get from start to end

            # Check if path exists
            if not path or path[0] != start:
                return {"path": "[]", "cost": 0}

            return {
                "path": json.dumps(path),
                "cost": distances[end]
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in graph data: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error in graph_shortest_path: {str(e)}")

    # --- Crypto (Simplified) ---
    def crypto_aes_cbc_decrypt(self, inputs):
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数 (使用模板中定义的参数名)
        hex_cipher = inputs.get("hex_cipher")
        hex_key = inputs.get("hex_key")
        hex_iv = inputs.get("hex_iv")

        # 类型检查
        if hex_cipher is not None and not isinstance(hex_cipher, str):
            raise TypeError("hex_cipher must be a string")

        if hex_key is not None and not isinstance(hex_key, str):
            raise TypeError("hex_key must be a string")

        if hex_iv is not None and not isinstance(hex_iv, str):
            raise TypeError("hex_iv must be a string")

        # 检查必需参数
        if hex_cipher is None:
            raise ValueError("hex_cipher parameter is required")

        if hex_key is None:
            raise ValueError("hex_key parameter is required")

        if hex_iv is None:
            raise ValueError("hex_iv parameter is required")

        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import padding

        try:
            # Convert hex strings to bytes
            ciphertext = bytes.fromhex(hex_cipher)
            key = bytes.fromhex(hex_key)
            iv = bytes.fromhex(hex_iv)

            # Validate key length (AES-128, AES-192, AES-256)
            if len(key) not in [16, 24, 32]:
                raise ValueError("Invalid key length. Must be 16, 24, or 32 bytes.")

            if len(iv) != 16:
                raise ValueError("Invalid IV length. Must be 16 bytes.")

            # Create cipher object
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )

            decryptor = cipher.decryptor()

            # Decrypt the ciphertext
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # Remove PKCS7 padding
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

            # Return decrypted text
            return {"text": plaintext.decode('utf-8', errors='ignore')}
        except ValueError as e:
            if "non-hexadecimal number found in fromhex()" in str(e):
                raise ValueError("Invalid hexadecimal string in hex_cipher, hex_key, or hex_iv")
            else:
                raise e
        except Exception as e:
            raise RuntimeError(f"Error in crypto_aes_cbc_decrypt: {str(e)}")

    def crypto_rsa_decrypt_hex(self, inputs):
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        hex_cipher = inputs.get("hex_cipher")
        n = inputs.get("n")
        d = inputs.get("d")

        # 类型检查
        if hex_cipher is not None and not isinstance(hex_cipher, str):
            raise TypeError("hex_cipher must be a string")
        if n is not None and not isinstance(n, (int, str)):
            raise TypeError("n must be an integer or string")
        if d is not None and not isinstance(d, (int, str)):
            raise TypeError("d must be an integer or string")

        # 检查必需参数
        if hex_cipher is None:
            raise ValueError("hex_cipher parameter is required")
        if n is None:
            raise ValueError("n parameter is required")
        if d is None:
            raise ValueError("d parameter is required")

        try:
            # Convert parameters to appropriate types
            cipher_int = int(hex_cipher, 16)
            n_int = int(n) if isinstance(n, str) else n
            d_int = int(d) if isinstance(d, str) else d

            # RSA decryption: plaintext = ciphertext^d mod n
            plaintext_int = pow(cipher_int, d_int, n_int)

            # Convert result to hex and then to text
            plaintext_hex = hex(plaintext_int)[2:]

            # Pad with leading zero if odd length
            if len(plaintext_hex) % 2 != 0:
                plaintext_hex = '0' + plaintext_hex

            # Convert hex to bytes and then to text
            try:
                plaintext_bytes = bytes.fromhex(plaintext_hex)
                plaintext_text = plaintext_bytes.decode('utf-8', errors='ignore')
            except:
                # If decoding fails, return hex representation
                plaintext_text = plaintext_hex

            return {"text": plaintext_text}
        except ValueError as e:
            if "non-hexadecimal number found" in str(e):
                raise ValueError("Invalid hexadecimal string in hex_cipher")
            else:
                raise ValueError(f"Invalid input values: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error in crypto_rsa_decrypt_hex: {str(e)}")

    # --- Others ---
    def num_base_convert(self, inputs):
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        s = inputs.get("s")
        from_base = inputs.get("from_base")
        to_base = inputs.get("to_base")

        # 类型检查 - 接受 str 或 int
        if s is not None and not isinstance(s, (str, int)):
            raise TypeError("s must be a string or integer")

        if from_base is not None and not isinstance(from_base, (int, str)):
            raise TypeError("from_base must be an integer")

        if to_base is not None and not isinstance(to_base, (int, str)):
            raise TypeError("to_base must be an integer")

        # 检查必需参数
        if s is None:
            raise ValueError("s parameter is required")

        if from_base is None:
            raise ValueError("from_base parameter is required")

        if to_base is None:
            raise ValueError("to_base parameter is required")

        try:
            # Convert to int if needed
            from_base = int(from_base) if isinstance(from_base, str) else from_base
            to_base = int(to_base) if isinstance(to_base, str) else to_base
            s_str = str(s)

            # 验证基数范围
            if from_base < 2 or from_base > 36:
                # 在 DAG 生成阶段，如果基数无效，返回输入值本身以保持数据流
                return {"str": s_str}

            if to_base < 2 or to_base > 36:
                # 在 DAG 生成阶段，如果基数无效，返回输入值本身以保持数据流
                return {"str": s_str}

            # Convert from source base to decimal
            val = int(s_str, from_base)

            # Convert from decimal to target base
            if to_base == 10:
                result = str(val)
            elif to_base == 16:
                result = hex(val)[2:]
            elif to_base == 8:
                result = oct(val)[2:]
            elif to_base == 2:
                result = bin(val)[2:]
            else:
                # Generic base conversion for other bases
                if val == 0:
                    result = "0"
                else:
                    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
                    result = ""
                    n = abs(val)
                    while n:
                        result = digits[n % to_base] + result
                        n //= to_base
                    if val < 0:
                        result = "-" + result

            return {"str": result}
        except ValueError as e:
            raise ValueError(f"Invalid number format: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error in num_base_convert: {str(e)}")

    def time_convert(self, inputs):
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        iso = inputs.get("iso")
        timestamp = inputs.get("timestamp")
        datetime_str = inputs.get("datetime")
        from_tz = inputs.get("from_tz")
        to_tz = inputs.get("to_tz")
        format_str = inputs.get("format")

        # 类型检查
        if iso is not None and not isinstance(iso, str):
            raise TypeError("iso must be a string")

        if timestamp is not None and not isinstance(timestamp, (str, int, float)):
            raise TypeError("timestamp must be a string, integer, or float")

        if datetime_str is not None and not isinstance(datetime_str, str):
            raise TypeError("datetime must be a string")

        if from_tz is not None and not isinstance(from_tz, str):
            raise TypeError("from_tz must be a string")

        if to_tz is not None and not isinstance(to_tz, str):
            raise TypeError("to_tz must be a string")

        if format_str is not None and not isinstance(format_str, str):
            raise TypeError("format must be a string")

        # 设置默认值
        if from_tz is None:
            from_tz = "UTC"

        if to_tz is None:
            to_tz = "UTC"

        import datetime
        import pytz

        # 验证时区参数
        try:
            if from_tz:
                pytz.timezone(from_tz)
            if to_tz:
                pytz.timezone(to_tz)
        except Exception:
            raise ValueError("Invalid timezone provided")

        try:
            # Parse input time
            dt = None

            if iso is not None:
                # Parse ISO 8601 format
                dt = datetime.datetime.fromisoformat(iso.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=pytz.UTC)
            elif timestamp is not None:
                # Parse Unix timestamp
                timestamp = float(timestamp)
                dt = datetime.datetime.fromtimestamp(timestamp, pytz.UTC)
            elif datetime_str is not None:
                # Parse datetime string
                # Try common formats
                formats_to_try = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d",
                    "%m/%d/%Y %H:%M:%S",
                    "%m/%d/%Y"
                ]

                parse_success = False
                for fmt in formats_to_try:
                    try:
                        dt = datetime.datetime.strptime(datetime_str, fmt)
                        dt = pytz.timezone(from_tz).localize(dt)
                        parse_success = True
                        break
                    except ValueError:
                        continue

                if not parse_success:
                    raise ValueError("Unable to parse datetime string with common formats")
            else:
                # 如果没有提供任何时间参数，则使用当前时间
                dt = datetime.datetime.now(pytz.UTC)
        except ValueError as e:
            raise ValueError(f"Error parsing time input: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error parsing time input: {str(e)}")

        try:
            # Convert timezone
            if from_tz != to_tz:
                dt = dt.astimezone(pytz.timezone(to_tz))

            # Format outputs
            result = {
                "iso": dt.isoformat(),
                "timestamp": str(dt.timestamp()),
                "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M:%S"),
                "timezone": to_tz
            }

            # Add custom format if requested
            if format_str:
                try:
                    result["formatted"] = dt.strftime(format_str)
                except ValueError as e:
                    raise ValueError(f"Invalid format string: {str(e)}")

            return result
        except Exception as e:
            raise RuntimeError(f"Error in time_convert: {str(e)}")

    def checksum_crc32(self, inputs):
        import zlib

        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        hex_data = inputs.get("hex")

        # 类型检查
        if hex_data is not None and not isinstance(hex_data, str):
            raise TypeError("hex must be a string")

        # 检查必需参数
        if hex_data is None:
            raise ValueError("hex parameter is required")

        try:
            # 验证十六进制字符串
            # 移除可能的空格
            hex_data = hex_data.replace(" ", "")

            # 检查是否为空
            if not hex_data:
                raise ValueError("hex data cannot be empty")

            # 检查是否为有效的十六进制字符串
            if not all(c in "0123456789abcdefABCDEF" for c in hex_data):
                raise ValueError("hex must be a valid hexadecimal string")

            # 检查长度是否为偶数
            if len(hex_data) % 2 != 0:
                raise ValueError("hex must have even number of characters")

            val = zlib.crc32(bytes.fromhex(hex_data))
            # 确保 hex 输出是 8 位，前导补 0
            return {"hex": f"{val:08x}", "int": val}
        except ValueError as e:
            if "non-hexadecimal number found" in str(e):
                raise ValueError("Invalid hexadecimal string")
            else:
                raise e
        except Exception as e:
            raise RuntimeError(f"Error in checksum_crc32: {str(e)}")

    def geo_haversine(self, inputs):
        import math

        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        lat1 = inputs.get("lat1")
        lon1 = inputs.get("lon1")
        lat2 = inputs.get("lat2")
        lon2 = inputs.get("lon2")

        # 类型检查
        if lat1 is not None and not isinstance(lat1, (int, float, str)):
            raise TypeError("lat1 must be a number or string")
        if lon1 is not None and not isinstance(lon1, (int, float, str)):
            raise TypeError("lon1 must be a number or string")
        if lat2 is not None and not isinstance(lat2, (int, float, str)):
            raise TypeError("lat2 must be a number or string")
        if lon2 is not None and not isinstance(lon2, (int, float, str)):
            raise TypeError("lon2 must be a number or string")

        # 检查必需参数
        if lat1 is None:
            raise ValueError("lat1 parameter is required")
        if lon1 is None:
            raise ValueError("lon1 parameter is required")
        if lat2 is None:
            raise ValueError("lat2 parameter is required")
        if lon2 is None:
            raise ValueError("lon2 parameter is required")

        try:
            # 转换为浮点数：如果本身就是数字就不用操作，如果是字符串就转成数字类型
            if isinstance(lat1, str):
                lat1 = float(lat1)
            elif not isinstance(lat1, (int, float)):
                raise TypeError("lat1 must be a number or string")
            else:
                lat1 = float(lat1)
            
            if isinstance(lon1, str):
                lon1 = float(lon1)
            elif not isinstance(lon1, (int, float)):
                raise TypeError("lon1 must be a number or string")
            else:
                lon1 = float(lon1)
            
            if isinstance(lat2, str):
                lat2 = float(lat2)
            elif not isinstance(lat2, (int, float)):
                raise TypeError("lat2 must be a number or string")
            else:
                lat2 = float(lat2)
            
            if isinstance(lon2, str):
                lon2 = float(lon2)
            elif not isinstance(lon2, (int, float)):
                raise TypeError("lon2 must be a number or string")
            else:
                lon2 = float(lon2)

            # Validate coordinates (approximate range check)
            if not (-90 <= lat1 <= 90):
                raise ValueError("lat1 must be between -90 and 90")
            if not (-90 <= lat2 <= 90):
                raise ValueError("lat2 must be between -90 and 90")
            if not (-180 <= lon1 <= 180):
                raise ValueError("lon1 must be between -180 and 180")
            if not (-180 <= lon2 <= 180):
                raise ValueError("lon2 must be between -180 and 180")

            # Earth radius in meters
            R = 6371000  # Approximate radius of Earth

            # Convert degrees to radians
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)

            # Calculate differences
            delta_lat = lat2_rad - lat1_rad
            delta_lon = lon2_rad - lon1_rad

            # Haversine formula
            a = math.sin(delta_lat / 2) ** 2 + \
                math.cos(lat1_rad) * math.cos(lat2_rad) * \
                math.sin(delta_lon / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance_m = R * c

            # Return distance in meters
            return {"meters": round(distance_m, 2)}
        except ValueError as e:
            raise ValueError(f"Invalid input values: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error in geo_haversine: {str(e)}")

    def otp_totp_generate(self, inputs):
        import hmac
        import hashlib
        import base64
        import time
        import struct

        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        base32_secret = inputs.get("base32_secret")
        step = inputs.get("step", 30)  # Default to 30 seconds
        digits = inputs.get("digits", 6)  # Default to 6 digits
        timestamp_iso = inputs.get("timestamp_iso", "")
        algo = inputs.get("algo", "sha1")  # Default to sha1 as current implementation only supports this

        # 类型检查
        if base32_secret is not None and not isinstance(base32_secret, str):
            raise TypeError("base32_secret must be a string")
        if not isinstance(step, (int, str)):
            raise TypeError("step must be an integer or string")
        if not isinstance(digits, (int, str)):
            raise TypeError("digits must be an integer or string")
        if not isinstance(timestamp_iso, str):
            raise TypeError("timestamp_iso must be a string")
        if not isinstance(algo, str):
            raise TypeError("algo must be a string")

        # 检查必需参数
        if base32_secret is None:
            raise ValueError("base32_secret parameter is required")

        try:
            # Convert step and digits to appropriate types
            step = int(step)
            digits = int(digits)
            if digits < 6 or digits > 8:
                raise ValueError("Digits must be between 6 and 8")

            # Convert timestamp_iso to integer timestamp
            if timestamp_iso:
                import datetime
                dt = datetime.datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00'))
                timestamp = int(dt.timestamp())
            else:
                timestamp = int(time.time())

            # Calculate counter value (T = floor(timestamp / step))
            counter = timestamp // step

            # Decode the base32 secret
            # Add padding if necessary (base64 requires padding to be multiple of 8)
            base32_secret = base32_secret.upper().replace(' ', '')
            if len(base32_secret) % 8 != 0:
                base32_secret += '=' * (8 - (len(base32_secret) % 8))
            key = base64.b32decode(base32_secret, casefold=True)

            # Calculate HMAC-SHA1
            counter_bytes = struct.pack('>Q', counter)  # Big-endian 8-byte integer
            hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()

            # Dynamic truncation
            offset = hmac_hash[-1] & 0xF
            code = struct.unpack('>I', hmac_hash[offset:offset+4])[0] & 0x7FFFFFFF

            # Generate the OTP
            otp = str(code % (10 ** digits)).zfill(digits)

            # Calculate remaining time until next OTP change
            remaining_time = step - (timestamp % step)

            return {"totp": otp, "remaining_time": remaining_time, "time_step": step}
        except ValueError as e:
            if "invalid literal for int()" in str(e):
                raise ValueError("step and digits must be valid integers")
            else:
                raise ValueError(f"Invalid input values: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error in otp_totp_generate: {str(e)}")

    def unicode_norm(self, inputs):
        import unicodedata

        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        text = inputs.get("text")
        form = inputs.get("form", "NFC")  # Default to NFC

        # 类型检查
        if text is not None and not isinstance(text, str):
            raise TypeError("text must be a string")
        if form is not None and not isinstance(form, str):
            raise TypeError("form must be a string")

        # 检查必需参数
        if text is None:
            raise ValueError("text parameter is required")

        try:
            # Normalize form (NFC, NFD, NFKC, NFKD)
            form = form.upper().strip()

            if form not in ['NFC', 'NFD', 'NFKC', 'NFKD']:
                raise ValueError(f"Invalid normalization form: {form}. Must be one of: NFC, NFD, NFKC, NFKD")

            # Apply Unicode normalization
            normalized_text = unicodedata.normalize(form, text)

            return {"text": normalized_text}
        except ValueError as e:
            raise ValueError(f"Invalid input values: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error in unicode_norm: {str(e)}")

    def text_bidi_sanitize(self, inputs):
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        text = inputs.get("text")

        # 类型检查
        if text is not None and not isinstance(text, str):
            raise TypeError("text must be a string")

        # 检查必需参数
        if text is None:
            raise ValueError("text parameter is required")

        try:
            # Bidi control characters to remove
            bidi_controls = [
                '\u200E',  # LEFT-TO-RIGHT MARK
                '\u200F',  # RIGHT-TO-LEFT MARK
                '\u202A',  # LEFT-TO-RIGHT EMBEDDING
                '\u202B',  # RIGHT-TO-LEFT EMBEDDING
                '\u202C',  # POP DIRECTIONAL FORMATTING
                '\u202D',  # LEFT-TO-RIGHT OVERRIDE
                '\u202E',  # RIGHT-TO-LEFT OVERRIDE
                '\u2066',  # LEFT-TO-RIGHT ISOLATE
                '\u2067',  # RIGHT-TO-LEFT ISOLATE
                '\u2068',  # FIRST STRONG ISOLATE
                '\u2069',  # POP DIRECTIONAL ISOLATE
            ]

            # Remove all Bidi control characters
            sanitized_text = text
            for control_char in bidi_controls:
                sanitized_text = sanitized_text.replace(control_char, '')

            return {"text": sanitized_text}
        except Exception as e:
            raise RuntimeError(f"Error in text_bidi_sanitize: {str(e)}")

    def text_xor_hex(self, inputs):
        import binascii

        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        hex_a = inputs.get("hex_a")
        hex_b = inputs.get("hex_b")

        # 类型检查
        if hex_a is not None and not isinstance(hex_a, str):
            raise TypeError("hex_a must be a string")
        if hex_b is not None and not isinstance(hex_b, str):
            raise TypeError("hex_b must be a string")

        # 检查必需参数
        if hex_a is None:
            raise ValueError("hex_a parameter is required")
        if hex_b is None:
            raise ValueError("hex_b parameter is required")

        try:
            # Remove any whitespace
            hex_a = hex_a.replace(" ", "").replace("\t", "").replace("\n", "").replace("\r", "")
            hex_b = hex_b.replace(" ", "").replace("\t", "").replace("\n", "").replace("\r", "")

            # Validate hex strings
            if not (all(c in "0123456789abcdefABCDEF" for c in hex_a) and len(hex_a) % 2 == 0):
                raise ValueError("hex_a must be a valid hexadecimal string with even length")
            if not (all(c in "0123456789abcdefABCDEF" for c in hex_b) and len(hex_b) % 2 == 0):
                raise ValueError("hex_b must be a valid hexadecimal string with even length")

            # Convert hex strings to bytes
            bytes_a = binascii.unhexlify(hex_a)
            bytes_b = binascii.unhexlify(hex_b)

            # Make the byte arrays the same length by padding the shorter one with zeros
            max_len = max(len(bytes_a), len(bytes_b))
            bytes_a = bytes_a.ljust(max_len, b'\x00')
            bytes_b = bytes_b.ljust(max_len, b'\x00')

            # Perform XOR operation
            result_bytes = bytes(a ^ b for a, b in zip(bytes_a, bytes_b))

            # Convert result back to hex
            result_hex = binascii.hexlify(result_bytes).decode('utf-8')

            return {"hex": result_hex}
        except ValueError as e:
            if "Non-hexadecimal digit found" in str(e):
                raise ValueError("Invalid hexadecimal string")
            else:
                raise ValueError(f"Invalid input values: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error in text_xor_hex: {str(e)}")

    def text_rotN(self, inputs):
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        text = inputs.get("text")
        n = inputs.get("n", 0)

        # 类型检查
        if text is not None and not isinstance(text, str):
            raise TypeError("text must be a string")
        if not isinstance(n, (int, str)):
            raise TypeError("n must be an integer or string")

        # 检查必需参数
        if text is None:
            raise ValueError("text parameter is required")

        try:
            n = int(n)
        except ValueError:
            raise ValueError("n must be a valid integer")

        result = []
        for char in text:
            if char.isupper():
                # Rotate uppercase letters
                result_char = chr((ord(char) - ord('A') + n) % 26 + ord('A'))
                result.append(result_char)
            elif char.islower():
                # Rotate lowercase letters
                result_char = chr((ord(char) - ord('a') + n) % 26 + ord('a'))
                result.append(result_char)
            else:
                # Keep non-alphabetic characters unchanged
                result.append(char)

        return {"text": ''.join(result)}

    def luhn_check(self, inputs):
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数（支持 card_number 和 number 两个参数名）
        card_number = inputs.get("number") or inputs.get("card_number")

        # 类型检查
        if card_number is not None and not isinstance(card_number, str):
            raise TypeError("number must be a string")

        # 检查必需参数
        if card_number is None:
            raise ValueError("number parameter is required")

        try:
            # 如果输入是JSON数组或其他非数字字符串，返回该字符串本身（用于数据传递）
            # 这种情况发生在DAG设计中类型不匹配时
            if card_number.startswith('[') or card_number.startswith('{'):
                # 输入是JSON，直接返回原值（用于传递）
                return {"valid": card_number}
            
            # Remove whitespace from card number
            card_number = card_number.replace(" ", "").replace("-", "")

            # Check if card number is all digits
            if not card_number.isdigit() or len(card_number) < 13:
                return {"valid": "false"}

            # Implement Luhn algorithm
            total = 0
            reverse_digits = card_number[::-1]  # Reverse the number for easier processing

            for i, digit in enumerate(reverse_digits):
                num = int(digit)
                if i % 2 == 1:  # Every second digit starting from the right (which is first in reversed string)
                    num *= 2
                    if num > 9:
                        num -= 9  # Equivalent to sum of digits for 2-digit numbers
                total += num

            # Check if total is divisible by 10
            is_valid = total % 10 == 0
            return {"valid": "true" if is_valid else "false"}
        except Exception as e:
            raise RuntimeError(f"Error in luhn_check: {str(e)}")

    def iban_validate(self, inputs):
        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        iban = inputs.get("iban")

        # 类型检查
        if iban is not None and not isinstance(iban, str):
            raise TypeError("iban must be a string")

        # 检查必需参数
        if iban is None:
            raise ValueError("iban parameter is required")

        try:
            # Remove whitespace from IBAN
            iban = iban.replace(" ", "")

            # Basic length and format check
            if not (len(iban) >= 15 and len(iban) <= 34):
                return {"valid": "False"}

            if not (iban[:2].isalpha() and iban[2:].isdigit()):
                return {"valid": "False"}

            # Move first four characters to the end
            rearranged = iban[4:] + iban[:4]

            # Replace letters with numbers (A=10, B=11, ..., Z=35)
            numeric_iban = ''
            for char in rearranged:
                if char.isdigit():
                    numeric_iban += char
                else:
                    numeric_iban += str(ord(char.upper()) - ord('A') + 10)

            # Perform modulo 97 check
            # Use step-by-step approach for very large numbers
            remainder = 0
            for char in numeric_iban:
                remainder = (remainder * 10 + int(char)) % 97

            is_valid = remainder == 1
            return {"valid": "True" if is_valid else "False"}
        except Exception as e:
            raise RuntimeError(f"Error in iban_validate: {str(e)}")

    def matter_synthesizer(self, inputs):
        import hashlib

        # 参数检查
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")

        # 获取参数
        blueprint = inputs.get("blueprint")

        # 类型检查
        if blueprint is not None and not isinstance(blueprint, str):
            raise TypeError("blueprint must be a string")

        try:
            # Get blueprint parameter as defined in interface
            if blueprint is None:
                blueprint = ""

            # Generate a unique item ID based on the blueprint
            # This ensures the same blueprint always produces the same item
            blueprint_hash = hashlib.sha256(blueprint.encode()).hexdigest()[:16]

            # Create a synthesized item with a deterministic ID based on blueprint
            synthesized_item = f"synthesized_item_{blueprint_hash}"

            return {"output_slot": synthesized_item}
        except Exception as e:
            raise RuntimeError(f"Error in matter_synthesizer: {str(e)}")

    # --- Terminal Implementations ---
    def terminal_1(self, inputs):
        """
        terminal_1: Terminal 节点，根据输入参数的正确性返回对应的输出
        
        逻辑：
        - 只输入正确的 slot_a → 只返回 text_output
        - 只输入正确的 slot_b → 只返回 hex_output
        - 同时输入正确的 slot_a 和 slot_b → 返回 item_dispenser（物品掉落）
        - 输入错误 → 返回错误信息
        
        在离线 DAG 生成阶段，golden_outputs 存在但 golden_inputs 为空，直接返回所有 outputs。
        在运行时评测阶段，golden_inputs 和 golden_outputs 都存在，根据输入验证返回对应输出。
        """
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        
        # 判断是否在 DAG 生成阶段（使用 _init_* 参数）
        # DAG 生成阶段：直接返回所有 init_outputs，不进行参数验证
        # 因为 init_inputs 可能只包含部分参数，其他参数从上游节点传递
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation:
            return dict(golden_outputs)
        
        # 评测阶段但没有 golden_inputs，也直接返回 outputs
        if not golden_inputs:
            return dict(golden_outputs)
        
        # 运行时评测阶段：根据输入验证返回对应输出
        slot_a = inputs.get("slot_a")
        slot_b = inputs.get("slot_b")
        
        # 检查哪些输入被提供了
        has_a = slot_a is not None and slot_a != ""
        has_b = slot_b is not None and slot_b != ""
        
        # 验证输入值是否正确（与 golden values 比较）
        a_valid = False
        b_valid = False
        
        if has_a and "slot_a" in golden_inputs:
            expected_a = golden_inputs["slot_a"]
            a_valid = str(slot_a) == str(expected_a)
        
        if has_b and "slot_b" in golden_inputs:
            expected_b = golden_inputs["slot_b"]
            b_valid = str(slot_b) == str(expected_b)
        
        # 根据验证结果返回对应的输出
        result = {}
        
        # 如果同时提供了两个输入且都正确 → 返回 item_dispenser
        if has_a and has_b:
            if a_valid and b_valid:
                if "item_dispenser" in golden_outputs:
                    result["item_dispenser"] = golden_outputs["item_dispenser"]
                return result
            else:
                # 至少有一个输入错误
                incorrect_params = []
                correct_params = []
                if not a_valid:
                    incorrect_params.append("slot_a")
                else:
                    correct_params.append("slot_a")
                if not b_valid:
                    incorrect_params.append("slot_b")
                else:
                    correct_params.append("slot_b")
                
                error_msg = f"Input validation failed. Incorrect parameters: {', '.join(incorrect_params)}"
                if correct_params:
                    error_msg += f". Correct parameters: {', '.join(correct_params)}"
                return {"error": error_msg}
        
        # 只提供 slot_a 且正确 → 返回 text_output
        if has_a and not has_b:
            if a_valid:
                if "text_output" in golden_outputs:
                    result["text_output"] = golden_outputs["text_output"]
                return result
            else:
                return {"error": "Input validation failed. Incorrect parameters: slot_a"}
        
        # 只提供 slot_b 且正确 → 返回 hex_output
        if has_b and not has_a:
            if b_valid:
                if "hex_output" in golden_outputs:
                    result["hex_output"] = golden_outputs["hex_output"]
                return result
            else:
                return {"error": "Input validation failed. Incorrect parameters: slot_b"}
        
        # 没有提供任何输入
        return {"error": "No valid inputs provided"}
    
    def terminal_2(self, inputs):
        """
        terminal_2: Terminal 节点，根据输入参数的正确性返回对应的输出
        
        逻辑：
        - 只输入正确的 num1 或 num2（任一）→ 返回 text_result
        - 同时输入正确的 num1 和 num2 → 返回 hex_result 和 math_token
        - 输入错误 → 返回错误信息
        
        在离线 DAG 生成阶段，golden_outputs 存在但 golden_inputs 为空，直接返回所有 outputs。
        在运行时评测阶段，golden_inputs 和 golden_outputs 都存在，根据输入验证返回对应输出。
        """
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        
        # 判断是否在 DAG 生成阶段（使用 _init_* 参数）
        # DAG 生成阶段：直接返回所有 init_outputs，不进行参数验证
        # 因为 init_inputs 可能只包含部分参数，其他参数从上游节点传递
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation:
            return dict(golden_outputs)
        
        # 评测阶段但没有 golden_inputs，也直接返回 outputs
        if not golden_inputs:
            return dict(golden_outputs)
        
        # 运行时评测阶段：根据输入验证返回对应输出
        num1 = inputs.get("num1")
        num2 = inputs.get("num2")
        
        # 检查哪些输入被提供了
        has_num1 = num1 is not None and num1 != ""
        has_num2 = num2 is not None and num2 != ""
        
        # 验证输入值是否正确（与 golden values 比较）
        num1_valid = False
        num2_valid = False
        
        if has_num1 and "num1" in golden_inputs:
            expected_num1 = golden_inputs["num1"]
            num1_valid = str(num1) == str(expected_num1)
        
        if has_num2 and "num2" in golden_inputs:
            expected_num2 = golden_inputs["num2"]
            num2_valid = str(num2) == str(expected_num2)
        
        # 根据验证结果返回对应的输出
        result = {}
        
        # 如果同时提供了两个输入且都正确 → 返回 hex_result 和 math_token
        if has_num1 and has_num2:
            if num1_valid and num2_valid:
                if "hex_result" in golden_outputs:
                    result["hex_result"] = golden_outputs["hex_result"]
                if "math_token" in golden_outputs:
                    result["math_token"] = golden_outputs["math_token"]
                return result
            else:
                # 至少有一个输入错误
                incorrect_params = []
                correct_params = []
                if not num1_valid:
                    incorrect_params.append("num1")
                else:
                    correct_params.append("num1")
                if not num2_valid:
                    incorrect_params.append("num2")
                else:
                    correct_params.append("num2")
                
                error_msg = f"Input validation failed. Incorrect parameters: {', '.join(incorrect_params)}"
                if correct_params:
                    error_msg += f". Correct parameters: {', '.join(correct_params)}"
                return {"error": error_msg}
        
        # 只提供一个输入且正确 → 返回 text_result
        if (has_num1 or has_num2):
            if (has_num1 and num1_valid) or (has_num2 and num2_valid):
                if "text_result" in golden_outputs:
                    result["text_result"] = golden_outputs["text_result"]
                return result
            else:
                if has_num1 and not num1_valid:
                    return {"error": "Input validation failed. Incorrect parameters: num1"}
                if has_num2 and not num2_valid:
                    return {"error": "Input validation failed. Incorrect parameters: num2"}
        
        # 没有提供任何输入
        return {"error": "No valid inputs provided"}
    
    def logic_terminal(self, inputs):
        """
        Logic Terminal: 根据输入参数的正确性返回对应的输出
        
        逻辑：
        - 只输入正确的 slot_a → 返回 screen（部分输出）
        - 只输入正确的 slot_b → 返回 screen 和 secondary_output
        - 同时输入正确的 slot_a 和 slot_b → 返回 screen, secondary_output, item_dispenser
        - 输入错误 → 返回错误信息
        
        在离线 DAG 生成阶段，golden_outputs 存在但 golden_inputs 为空，直接返回所有 outputs。
        在运行时评测阶段，golden_inputs 和 golden_outputs 都存在，根据输入验证返回对应输出。
        """
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        
        # 判断是否在 DAG 生成阶段（使用 _init_* 参数）
        # DAG 生成阶段：直接返回所有 init_outputs，不进行参数验证
        # 因为 init_inputs 可能只包含部分参数，其他参数从上游节点传递
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation:
            return dict(golden_outputs)
        
        # 评测阶段但没有 golden_inputs，也直接返回 outputs
        if not golden_inputs:
            return dict(golden_outputs)
        
        # 运行时评测阶段：根据输入验证返回对应输出
        slot_a = inputs.get("slot_a")
        slot_b = inputs.get("slot_b")

        has_a = slot_a is not None and slot_a != ""
        has_b = slot_b is not None and slot_b != ""
        
        # 验证输入值（与 golden values 比较）
        a_valid = False
        b_valid = False
        
        if has_a and "slot_a" in golden_inputs:
            a_valid = str(slot_a) == str(golden_inputs["slot_a"])
        
        if has_b and "slot_b" in golden_inputs:
            b_valid = str(slot_b) == str(golden_inputs["slot_b"])

        result = {}
        
        # 同时提供两个输入且都正确 → 返回所有输出（包括 item_dispenser）
        if has_a and has_b:
            if a_valid and b_valid:
                if "screen" in golden_outputs:
                    result["screen"] = golden_outputs["screen"]
                if "secondary_output" in golden_outputs:
                    result["secondary_output"] = golden_outputs["secondary_output"]
                if "item_dispenser" in golden_outputs:
                    result["item_dispenser"] = golden_outputs["item_dispenser"]
                return result
            else:
                incorrect_params = []
                correct_params = []
                if not a_valid:
                    incorrect_params.append("slot_a")
                else:
                    correct_params.append("slot_a")
                if not b_valid:
                    incorrect_params.append("slot_b")
                else:
                    correct_params.append("slot_b")
                
                error_msg = f"Input validation failed. Incorrect parameters: {', '.join(incorrect_params)}"
                if correct_params:
                    error_msg += f". Correct parameters: {', '.join(correct_params)}"
                return {"error": error_msg}
        
        # 只提供 slot_a 且正确 → 返回 screen（部分输出）
        if has_a and not has_b:
            if a_valid:
                if "screen" in golden_outputs:
                    result["screen"] = golden_outputs["screen"]
                return result
            else:
                return {"error": "Input validation failed. Incorrect parameters: slot_a"}
        
        # 只提供 slot_b 且正确 → 返回 screen 和 secondary_output
        if has_b and not has_a:
            if b_valid:
                if "screen" in golden_outputs:
                    result["screen"] = golden_outputs["screen"]
                if "secondary_output" in golden_outputs:
                    result["secondary_output"] = golden_outputs["secondary_output"]
                return result
            else:
                return {"error": "Input validation failed. Incorrect parameters: slot_b"}
        
        # 没有提供任何输入
        return {"error": "No valid inputs provided"}
    
    def math_terminal(self, inputs):
        """
        Math Terminal: 根据输入参数的正确性返回对应的输出
        
        逻辑：
        - 只输入正确的 num1 或 num2（任一）→ 返回 result_display
        - 同时输入正确的 num1 和 num2 → 返回 result_display, hex_result, math_token
        - 输入错误 → 返回错误信息
        
        在离线 DAG 生成阶段，golden_outputs 存在但 golden_inputs 为空，直接返回所有 outputs。
        在运行时评测阶段，golden_inputs 和 golden_outputs 都存在，根据输入验证返回对应输出。
        """
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        
        # 判断是否在 DAG 生成阶段（使用 _init_* 参数）
        # DAG 生成阶段：直接返回所有 init_outputs，不进行参数验证
        # 因为 init_inputs 可能只包含部分参数，其他参数从上游节点传递
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation:
            return dict(golden_outputs)
        
        # 评测阶段但没有 golden_inputs，也直接返回 outputs
        if not golden_inputs:
            return dict(golden_outputs)
        
        # 运行时评测阶段：根据输入验证返回对应输出
        num1 = inputs.get("num1")
        num2 = inputs.get("num2")

        has_num1 = num1 is not None and num1 != ""
        has_num2 = num2 is not None and num2 != ""
        
        # 验证输入值（与 golden values 比较）
        num1_valid = False
        num2_valid = False
        
        if has_num1 and "num1" in golden_inputs:
            num1_valid = str(num1) == str(golden_inputs["num1"])
        
        if has_num2 and "num2" in golden_inputs:
            num2_valid = str(num2) == str(golden_inputs["num2"])
        
        result = {}
        
        # 同时提供两个输入且都正确 → 返回所有输出
        if has_num1 and has_num2:
            if num1_valid and num2_valid:
                if "result_display" in golden_outputs:
                    result["result_display"] = golden_outputs["result_display"]
                if "hex_result" in golden_outputs:
                    result["hex_result"] = golden_outputs["hex_result"]
                if "math_token" in golden_outputs:
                    result["math_token"] = golden_outputs["math_token"]
                return result
            else:
                incorrect_params = []
                correct_params = []
                if not num1_valid:
                    incorrect_params.append("num1")
                else:
                    correct_params.append("num1")
                if not num2_valid:
                    incorrect_params.append("num2")
                else:
                    correct_params.append("num2")
                
                error_msg = f"Input validation failed. Incorrect parameters: {', '.join(incorrect_params)}"
                if correct_params:
                    error_msg += f". Correct parameters: {', '.join(correct_params)}"
                return {"error": error_msg}
        
        # 只提供一个输入且正确 → 返回 result_display
        if (has_num1 or has_num2):
            if (has_num1 and num1_valid) or (has_num2 and num2_valid):
                if "result_display" in golden_outputs:
                    result["result_display"] = golden_outputs["result_display"]
                return result
            else:
                if has_num1 and not num1_valid:
                    return {"error": "Input validation failed. Incorrect parameters: num1"}
                if has_num2 and not num2_valid:
                    return {"error": "Input validation failed. Incorrect parameters: num2"}
        
        # 没有提供任何输入
        return {"error": "No valid inputs provided"}

    def crypt_terminal(self, inputs):
        """
        Encryption Terminal: 根据输入参数的正确性返回对应的输出
        
        逻辑：
        - 只输入正确的 plaintext → 返回 status（部分输出）
        - 同时输入正确的 plaintext 和 key → 返回 status, encrypted_hex, encryption_chip
        - 输入错误 → 返回错误信息
        
        在离线 DAG 生成阶段，golden_outputs 存在但 golden_inputs 为空，直接返回所有 outputs。
        在运行时评测阶段，golden_inputs 和 golden_outputs 都存在，根据输入验证返回对应输出。
        """
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        
        # 判断是否在 DAG 生成阶段（使用 _init_* 参数）
        # DAG 生成阶段：直接返回所有 init_outputs，不进行参数验证
        # 因为 init_inputs 可能只包含部分参数，其他参数从上游节点传递
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation:
            return dict(golden_outputs)
        
        # 评测阶段但没有 golden_inputs，也直接返回 outputs
        if not golden_inputs:
            return dict(golden_outputs)
        
        # 运行时评测阶段：根据输入验证返回对应输出
        plaintext = inputs.get("plaintext")
        key = inputs.get("key")

        has_plaintext = plaintext is not None and plaintext != ""
        has_key = key is not None and key != ""
        
        # 验证输入值（与 golden values 比较）
        plaintext_valid = False
        key_valid = False
        
        if has_plaintext and "plaintext" in golden_inputs:
            plaintext_valid = str(plaintext) == str(golden_inputs["plaintext"])
        
        if has_key and "key" in golden_inputs:
            key_valid = str(key) == str(golden_inputs["key"])
        
        result = {}
        
        # 同时提供两个输入且都正确 → 返回所有输出
        if has_plaintext and has_key:
            if plaintext_valid and key_valid:
                if "status" in golden_outputs:
                    result["status"] = golden_outputs["status"]
                if "encrypted_hex" in golden_outputs:
                    result["encrypted_hex"] = golden_outputs["encrypted_hex"]
                if "encryption_chip" in golden_outputs:
                    result["encryption_chip"] = golden_outputs["encryption_chip"]
                return result
            else:
                incorrect_params = []
                correct_params = []
                if not plaintext_valid:
                    incorrect_params.append("plaintext")
                else:
                    correct_params.append("plaintext")
                if not key_valid:
                    incorrect_params.append("key")
                else:
                    correct_params.append("key")
                
                error_msg = f"Input validation failed. Incorrect parameters: {', '.join(incorrect_params)}"
                if correct_params:
                    error_msg += f". Correct parameters: {', '.join(correct_params)}"
                return {"error": error_msg}
        
        # 只提供 plaintext 且正确 → 返回 status（部分输出）
        if has_plaintext and not has_key:
            if plaintext_valid:
                if "status" in golden_outputs:
                    result["status"] = golden_outputs["status"]
                return result
            else:
                return {"error": "Input validation failed. Incorrect parameters: plaintext"}
        
        # 只提供 key 但没有 plaintext
        if has_key and not has_plaintext:
            return {"error": "plaintext required"}
        
        # 没有提供任何输入
        return {"error": "No valid inputs provided"}
    def sequence_terminal(self, inputs):
        """
        Sequence Terminal: 根据输入参数的正确性返回对应的输出
        
        逻辑：
        - 只输入正确的 sequence → 返回 verification（部分输出）
        - 同时输入正确的 sequence 和 checksum → 返回 verification, auth_code, access_card
        - 输入错误 → 返回错误信息
        
        在离线 DAG 生成阶段，golden_outputs 存在但 golden_inputs 为空，直接返回所有 outputs。
        在运行时评测阶段，golden_inputs 和 golden_outputs 都存在，根据输入验证返回对应输出。
        """
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        
        # 判断是否在 DAG 生成阶段（使用 _init_* 参数）
        # DAG 生成阶段：直接返回所有 init_outputs，不进行参数验证
        # 因为 init_inputs 可能只包含部分参数，其他参数从上游节点传递
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation:
            return dict(golden_outputs)
        
        # 评测阶段但没有 golden_inputs，也直接返回 outputs
        if not golden_inputs:
            return dict(golden_outputs)
        
        # 运行时评测阶段：根据输入验证返回对应输出
        sequence = inputs.get("sequence")
        checksum = inputs.get("checksum")

        has_sequence = sequence is not None and sequence != ""
        has_checksum = checksum is not None and checksum != ""
        
        # 验证输入值（与 golden values 比较）
        sequence_valid = False
        checksum_valid = False
        
        if has_sequence and "sequence" in golden_inputs:
            sequence_valid = str(sequence) == str(golden_inputs["sequence"])
        
        if has_checksum and "checksum" in golden_inputs:
            checksum_valid = str(checksum) == str(golden_inputs["checksum"])
        
        result = {}
        
        # 同时提供两个输入且都正确 → 返回所有输出
        if has_sequence and has_checksum:
            if sequence_valid and checksum_valid:
                if "verification" in golden_outputs:
                    result["verification"] = golden_outputs["verification"]
                if "auth_code" in golden_outputs:
                    result["auth_code"] = golden_outputs["auth_code"]
                if "access_card" in golden_outputs:
                    result["access_card"] = golden_outputs["access_card"]
                return result
            else:
                incorrect_params = []
                correct_params = []
                if not sequence_valid:
                    incorrect_params.append("sequence")
                else:
                    correct_params.append("sequence")
                if not checksum_valid:
                    incorrect_params.append("checksum")
                else:
                    correct_params.append("checksum")
                
                error_msg = f"Input validation failed. Incorrect parameters: {', '.join(incorrect_params)}"
                if correct_params:
                    error_msg += f". Correct parameters: {', '.join(correct_params)}"
                return {"error": error_msg}
        
        # 只提供 sequence 且正确 → 返回 verification（部分输出）
        if has_sequence and not has_checksum:
            if sequence_valid:
                if "verification" in golden_outputs:
                    result["verification"] = golden_outputs["verification"]
                return result
            else:
                return {"error": "Input validation failed. Incorrect parameters: sequence"}
        
        # 只提供 checksum 但没有 sequence
        if has_checksum and not has_sequence:
            return {"error": "sequence required"}
        
        # 没有提供任何输入
        return {"error": "No valid inputs provided"}
    
    # --- Additional File Tools ---
    
    def zip_unzip_file(self, inputs):
        """ZIP 解压文件工具（模拟）
        
        在 DAG 生成阶段，直接返回 init_outputs，不验证输入。
        在运行时评测阶段，验证输入并返回对应输出。
        """
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        
        # 判断是否在 DAG 生成阶段
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation:
            return dict(golden_outputs)
        
        # 评测阶段但没有 golden_inputs，也直接返回 outputs
        if not golden_inputs:
            return dict(golden_outputs)
        
        # 运行时评测阶段：验证输入
        zip_id = inputs.get("zip_id")
        password = inputs.get("password")
        
        has_zip_id = zip_id is not None and zip_id != ""
        has_password = password is not None and password != ""
        
        # 验证输入值（与 golden values 比较）
        zip_id_valid = False
        password_valid = False
        
        if has_zip_id and "zip_id" in golden_inputs:
            zip_id_valid = str(zip_id) == str(golden_inputs["zip_id"])
        
        if has_password and "password" in golden_inputs:
            password_valid = str(password) == str(golden_inputs["password"])
        
        # 两个输入都提供且都正确 → 返回所有输出
        if has_zip_id and has_password:
            if zip_id_valid and password_valid:
                return dict(golden_outputs)
            else:
                incorrect_params = []
                correct_params = []
                if not zip_id_valid:
                    incorrect_params.append("zip_id")
                else:
                    correct_params.append("zip_id")
                if not password_valid:
                    incorrect_params.append("password")
                else:
                    correct_params.append("password")
                
                error_msg = f"Input validation failed. Incorrect parameters: {', '.join(incorrect_params)}"
                if correct_params:
                    error_msg += f". Correct parameters: {', '.join(correct_params)}"
                return {"error": error_msg}
        
        # 没有提供完整输入
        missing = []
        if not has_zip_id:
            missing.append("zip_id")
        if not has_password:
            missing.append("password")
        return {"error": "Missing required inputs: " + ", ".join(missing)}
    
    def zip_unzip_item(self, inputs):
        """ZIP 解压道具工具（模拟）
        
        在 DAG 生成阶段，直接返回 init_outputs，不验证输入。
        在运行时评测阶段，验证输入并返回对应输出。
        """
        # 优先使用 _golden_*，如果不存在则回退到 _init_*
        golden_outputs = inputs.get("_golden_outputs") or inputs.get("_init_outputs", {})
        golden_inputs = inputs.get("_golden_inputs") or inputs.get("_init_inputs", {})
        
        # 判断是否在 DAG 生成阶段
        is_dag_generation = "_init_outputs" in inputs and "_golden_outputs" not in inputs
        
        if is_dag_generation:
            return dict(golden_outputs)
        
        # 评测阶段但没有 golden_inputs，也直接返回 outputs
        if not golden_inputs:
            return dict(golden_outputs)
        
        # 运行时评测阶段：验证输入
        zip_id = inputs.get("zip_id")
        password = inputs.get("password")
        
        has_zip_id = zip_id is not None and zip_id != ""
        has_password = password is not None and password != ""
        
        # 验证输入值（与 golden values 比较）
        zip_id_valid = False
        password_valid = False
        
        if has_zip_id and "zip_id" in golden_inputs:
            zip_id_valid = str(zip_id) == str(golden_inputs["zip_id"])
        
        if has_password and "password" in golden_inputs:
            password_valid = str(password) == str(golden_inputs["password"])
        
        # 两个输入都提供且都正确 → 返回所有输出
        if has_zip_id and has_password:
            if zip_id_valid and password_valid:
                return dict(golden_outputs)
            else:
                incorrect_params = []
                correct_params = []
                if not zip_id_valid:
                    incorrect_params.append("zip_id")
                else:
                    correct_params.append("zip_id")
                if not password_valid:
                    incorrect_params.append("password")
                else:
                    correct_params.append("password")
                
                error_msg = f"Input validation failed. Incorrect parameters: {', '.join(incorrect_params)}"
                if correct_params:
                    error_msg += f". Correct parameters: {', '.join(correct_params)}"
                return {"error": error_msg}
        
        # 没有提供完整输入
        missing = []
        if not has_zip_id:
            missing.append("zip_id")
        if not has_password:
            missing.append("password")
        return {"error": "Missing required inputs: " + ", ".join(missing)}
    
    def code_py_exec(self, inputs):
        """Python 代码执行工具
        
        这是一个真实执行的工具，在 DAG 生成阶段和运行时评测阶段都会执行代码。
        输入: code (Python 代码字符串)
        输出: stdout (标准输出，包含执行结果和错误信息)
        
        特殊行为：
        - 如果代码定义了 main() 函数，会自动调用它
        - 如果执行出错，错误信息会包含在 stdout 中
        """
        code = inputs.get("code", "")
        
        if not code:
            return {"stdout": "Error: No code provided"}
        
        try:
            # 创建一个受限的执行环境
            import io
            import sys
            
            # 捕获标准输出和标准错误
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            
            # 执行代码
            exec_globals = {"__builtins__": __builtins__}
            exec_locals = {}
            exec(code, exec_globals, exec_locals)
            
            # 如果定义了 main() 函数，自动调用它
            if 'main' in exec_locals and callable(exec_locals['main']):
                exec_locals['main']()
            
            # 获取输出
            stdout_value = sys.stdout.getvalue()
            stderr_value = sys.stderr.getvalue()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # 合并 stdout 和 stderr
            output = stdout_value
            if stderr_value:
                output += ("\n" if output else "") + f"[stderr] {stderr_value}"
            
            # 如果没有任何输出，尝试返回 result 变量的值
            if not output:
                result = exec_locals.get("_result") or exec_locals.get("result")
                if result is not None:
                    output = str(result)
            
            return {"stdout": output if output else "(no output)"}
            
        except Exception as e:
            # 恢复标准输出和错误输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # 返回错误信息
            return {"stdout": f"Error: {type(e).__name__}: {str(e)}"}
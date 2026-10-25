from models import InterfaceType, Port

# 工具模板库
TOOL_TEMPLATES = [
    # ---------- 数论 / 大数 ----------
    {
        "id_template": "calc_bigmul",
        "name": "Big Number Multiplier",
        "description": "Multiply two (very large) decimal integers represented as strings.",
        "inputs": [
            Port(name="a", type=InterfaceType.BIG_INT, description="First large integer"),
            Port(name="b", type=InterfaceType.BIG_INT, description="Second large integer"),
        ],
        "outputs": [
            Port(name="product", type=InterfaceType.BIG_INT, description="Product result"),
        ],
    },
    # --- ModExp (BigInt & Int) ---
    {
        "id_template": "calc_modexp",
        "name": "BigInt Modular Exponentiation",
        "description": "Modular exponentiation pow(base, exp, mod) with large decimal strings.",
        "inputs": [
            Port(name="base", type=InterfaceType.BIG_INT, description="Base"),
            Port(name="exp", type=InterfaceType.BIG_INT, description="Exponent"),
            Port(name="mod", type=InterfaceType.BIG_INT, description="Modulus"),
        ],
        "outputs": [
            Port(name="value", type=InterfaceType.BIG_INT, description="Result value"),
        ],
    },
    # --- GCD (BigInt & Int) ---
    {
        "id_template": "calc_gcd",
        "name": "BigInt GCD Calculator",
        "description": "Greatest common divisor of two large decimal integers.",
        "inputs": [
            Port(name="a", type=InterfaceType.BIG_INT, description="First integer"),
            Port(name="b", type=InterfaceType.BIG_INT, description="Second integer"),
        ],
        "outputs": [
            Port(name="gcd", type=InterfaceType.BIG_INT, description="GCD result"),
        ],
    },
    # --- Modular Inverse (BigInt & Int) ---
    {
        "id_template": "calc_inv_mod",
        "name": "BigInt Modular Inverse",
        "description": "Modular inverse of a modulo mod (large decimal strings).",
        "inputs": [
            Port(name="a", type=InterfaceType.BIG_INT, description="Integer a"),
            Port(name="mod", type=InterfaceType.BIG_INT, description="Modulus"),
        ],
        "outputs": [
            Port(name="inv", type=InterfaceType.BIG_INT, description="Modular inverse"),
        ],
    },

    # ---------- 哈希 / HMAC ----------
    {
        "id_template": "hash_sha256",
        "name": "SHA-256 Hasher",
        "description": "SHA-256 over UTF-8 text; returns hex.",
        "inputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC，统一普通文本类型
                description="Text to hash",
            )
        ],
        "outputs": [
            # Port(name="hex", type=InterfaceType.HEX_STRING_HASH_SHA256, description="SHA-256 Hex digest")
            Port(name="hex", type=InterfaceType.HEX_STRING, description="SHA-256 Hex digest"),
        ],
    },
    {
        "id_template": "hash_md5",
        "name": "MD5 Hasher",
        "description": "MD5 over UTF-8 text; returns hex.",
        "inputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Text to hash",
            )
        ],
        "outputs": [
            # Port(name="hex", type=InterfaceType.HEX_STRING_HASH_MD5, description="MD5 Hex digest")
            Port(name="hex", type=InterfaceType.HEX_STRING, description="MD5 Hex digest"),
        ],
    },
    {
        "id_template": "hmac_sha256",
        "name": "HMAC-SHA256 Calculator",
        "description": "HMAC-SHA256(text) with hex key.",
        "inputs": [
            Port(name="hex_key", type=InterfaceType.HEX_STRING, description="Hex key"),
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Text message",
            ),
        ],
        "outputs": [
            # Port(name="hex", type=InterfaceType.HEX_STRING_HMAC, description="HMAC Hex digest")
            Port(name="hex", type=InterfaceType.HEX_STRING, description="HMAC Hex digest"),
        ],
    },

    # ---------- 编码 / 压缩 / 归档 ----------
    {
        "id_template": "base64_decode",
        "name": "Base64 Decoder",
        "description": "Decode base64 to hex bytes.",
        "inputs": [
            # Port(name="data", type=InterfaceType.BASE64_STRING, description="Base64 string")
            Port(
                name="data",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING 专门化为 TEXT_BASE64 的设计废弃，回退为 TEXT_GENERIC 以提高连通性
                description="Base64 string",
            )
        ],
        "outputs": [
            Port(name="bytes_hex", type=InterfaceType.HEX_STRING, description="Decoded bytes as Hex"),
        ],
    },
    {
        "id_template": "base64_encode",
        "name": "Base64 Encoder",
        "description": "Encode hex bytes to base64.",
        "inputs": [
            Port(name="hex", type=InterfaceType.HEX_STRING, description="Hex bytes"),
        ],
        "outputs": [
            # Port(name="b64", type=InterfaceType.BASE64_STRING, description="Base64 string")
            Port(
                name="b64",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING / TEXT_BASE64 -> TEXT_GENERIC
                description="Base64 string",
            )
        ],
    },
    {
        "id_template": "hex_decode",
        "name": "Hex to Text Decoder",
        "description": "Decode hex to UTF-8 text.",
        "inputs": [
            Port(name="hex", type=InterfaceType.HEX_STRING, description="Hex string"),
        ],
        "outputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Decoded text",
            )
        ],
    },
    {
        "id_template": "hex_encode",
        "name": "Text to Hex Encoder",
        "description": "Encode UTF-8 text to hex.",
        "inputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,
                description="Text",
            )
        ],
        "outputs": [
            Port(name="hex", type=InterfaceType.HEX_STRING, description="Encoded hex"),
        ],
    },
    {
        "id_template": "zlib_inflate",
        "name": "Zlib Inflate",
        "description": "Inflate zlib-compressed data (hex) to text.",
        "inputs": [
            # Port(name="hex", type=InterfaceType.ZLIB_HEX_STRING, description="Zlib compressed hex")
            Port(name="hex", type=InterfaceType.HEX_STRING, description="Zlib compressed hex"),
        ],
        "outputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Inflated text",
            )
        ],
    },
    {
        "id_template": "zlib_deflate",
        "name": "Zlib Deflate",
        "description": "Deflate text to zlib bytes (hex).",
        "inputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Text to compress",
            )
        ],
        "outputs": [
            # Port(name="hex", type=InterfaceType.ZLIB_HEX_STRING, description="Compressed hex")
            Port(name="hex", type=InterfaceType.HEX_STRING, description="Compressed hex"),
        ],
    },
    {
        "id_template": "zip_unzip_file",
        "name": "Zip Unzipper",
        "description": "Unzip a password-protected zip file by id.",
        "inputs": [
            Port(
                name="zip_id",
                type=InterfaceType.FILE_ID,  # 修改: 原 FILE_PATH_ZIP / FILE_ID_ZIP -> 统一为 FILE_ID，增强与其他文件工具的连接性
                description="Zip file ID",
            ),
            Port(
                name="password",
                type=InterfaceType.TEXT_GENERIC,
                description="Password",
            ),
        ],
        "outputs": [
            Port(
                name="files",
                type=InterfaceType.FILE_ID,  # 修改: 原 FILE_PATH / FILE_ID_GENERIC -> 统一为 FILE_ID
                description="Extracted file ID",
            )
        ],
    },
    {
        "id_template": "zip_unzip_item",
        "name": "Zip Unzipper",
        "description": "Unzip a password-protected zip file by id.",
        "inputs": [
            Port(
                name="zip_id",
                type=InterfaceType.FILE_ID,  # 修改: 原 FILE_PATH_ZIP / FILE_ID_ZIP -> 统一为 FILE_ID，增强与其他文件工具的连接性
                description="Zip file ID",
            ),
            Port(
                name="password",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Password",
            ),
        ],
        "outputs": [
            Port(
                name="item",
                type=InterfaceType.ITEM,
                description="item in the zip",
            )
        ],
    },

    # ---------- 文本 / 正则 / 结构化 ----------
    {
        "id_template": "regex_search",
        "name": "Regex Search",
        "description": "Search regex in either raw text or a file.",
        "inputs": [
            Port(
                name="pattern",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 TEXT_REGEX -> TEXT_GENERIC，避免孤立类型
                description="Regex pattern",
            ),
            Port(
                name="file_id",
                type=InterfaceType.FILE_ID,  # 修改: 原 FILE_PATH / FILE_ID_GENERIC -> FILE_ID
                description="File ID (optional)",
            ),
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Text (optional)",
            ),
        ],
        "outputs": [
            Port(
                name="matches",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Found matches (List)",
            )
        ],
    },
    {
        "id_template": "json_get",
        "name": "JSON Getter",
        "description": "Extract values by simple JSONPath.",
        "inputs": [
            Port(
                name="file_id",
                type=InterfaceType.FILE_ID,  # 修改: 原 FILE_PATH_JSON / FILE_ID_JSON -> FILE_ID
                description="JSON file ID",
            ),
            # Port(name="jsonpath", type=InterfaceType.JSON_PATH, description="JSONPath expression")
            Port(
                name="jsonpath",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 TEXT_JSONPATH -> TEXT_GENERIC
                description="JSONPath expression",
            ),
        ],
        "outputs": [
            Port(
                name="values",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Extracted values",
            )
        ],
    },
    {
        "id_template": "csv_query",
        "name": "CSV Query",
        "description": "Query CSV: select columns and simple WHERE.",
        "inputs": [
            Port(
                name="file_id",
                type=InterfaceType.FILE_ID,  # 修改: 原 FILE_PATH_CSV / FILE_ID_CSV -> FILE_ID
                description="CSV file ID",
            ),
            Port(
                name="select",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Columns to select",
            ),
            # Port(name="where", type=InterfaceType.SQL_WHERE, description="Where clause")
            Port(
                name="where",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 TEXT_SQL_WHERE -> TEXT_GENERIC
                description="Where clause",
            ),
        ],
        "outputs": [
            Port(
                name="rows",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Result rows",
            )
        ],
    },

    # ---------- 图 / 规划 ----------
    {
        "id_template": "graph_shortest_path",
        "name": "Shortest Path Finder",
        "description": "Shortest path on graph json file with edges list.",
        "inputs": [
            # Port(name="file_id", type=InterfaceType.FILE_PATH_GRAPH_JSON, description="Graph JSON file ID"),
            Port(
                name="file_id",
                type=InterfaceType.FILE_ID,  # 修改: 原 STRING / FILE_ID_GRAPH_JSON -> 统一为 FILE_ID
                description="Graph JSON file ID",
            ),
            Port(
                name="src",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Source node",
            ),
            Port(
                name="dst",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Destination node",
            ),
        ],
        "outputs": [
            Port(
                name="path",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Path list",
            ),
            Port(name="cost", type=InterfaceType.BIG_INT, description="Path cost"),
        ],
    },

    # ---------- 加解密 ----------
    {
        "id_template": "crypto_aes_cbc_decrypt",
        "name": "AES-CBC Decrypt",
        "description": "AES-CBC decrypt. hex_cipher/key/iv as hex.",
        "inputs": [
            Port(name="hex_cipher", type=InterfaceType.HEX_STRING, description="Ciphertext (Hex)"),
            Port(name="hex_key", type=InterfaceType.HEX_STRING_KEY_AES, description="AES Key (Hex)"),
            Port(name="hex_iv", type=InterfaceType.HEX_STRING_IV_AES, description="IV (Hex)"),
        ],
        "outputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Decrypted text",
            )
        ],
    },
    {
        "id_template": "crypto_rsa_decrypt_hex",
        "name": "RSA Decrypt",
        "description": "RSA decrypt (hex cipher) with n,d (decimal).",
        "inputs": [
            Port(name="hex_cipher", type=InterfaceType.HEX_STRING, description="Ciphertext (Hex)"),
            Port(name="n", type=InterfaceType.BIG_INT, description="Modulus n"),
            Port(name="d", type=InterfaceType.BIG_INT, description="Private exponent d"),
        ],
        "outputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 保留明文 TEXT_GENERIC，删除多余的 HEX_STRING 输出，简化类型
                description="Decrypted text",
            )
        ],
    },

    # ---------- 受限代码执行 ----------
    {
        "id_template": "code_py_exec",
        "name": "Python Executor",
        "description": "Run limited Python: only safe builtins.",
        "inputs": [
            # Port(name="code", type=InterfaceType.CODE_PYTHON, description="Python code")
            Port(
                name="code",
                type=InterfaceType.CODE_PYTHON,  # 修改: 原 TEXT_GENERIC / STRING -> CODE_PYTHON，严格区分代码和普通文本
                description="Python code",
            )
        ],
        "outputs": [
            # 修改: 合并 stdout / stderr，只保留一个 stdout
            Port(
                name="stdout",
                type=InterfaceType.TEXT_GENERIC,
                description="Standard Output (includes errors if any)",
            )
        ],
    },

    # ---------- 其他常用 ----------
    {
        "id_template": "num_base_convert",
        "name": "Base Converter",
        "description": "Convert integer between bases (2..36).",  # 文案略调：不再强调“string”
        "inputs": [
            Port(
                name="s",
                type=InterfaceType.BIG_INT,  # 修改: 原 TEXT_GENERIC -> INT，表示这里是数值语义而非普通文本
                description="Input integer value",
            ),
            Port(name="from_base", type=InterfaceType.BIG_INT, description="From base"),
            Port(name="to_base", type=InterfaceType.BIG_INT, description="To base"),
        ],
        "outputs": [
            Port(
                name="str",
                type=InterfaceType.BIG_INT,  # 修改: 原 STRING / TEXT_GENERIC -> INT，输出也统一为整数类型，便于继续数论计算
                description="Converted integer value",
            )
        ],
    },
    {
        "id_template": "time_convert",
        "name": "Timezone Converter",
        "description": "Convert ISO time between timezones.",
        "inputs": [
            Port(
                name="iso",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 TIMESTAMP_ISO -> TEXT_GENERIC，避免引入孤立时间类型
                description="ISO Timestamp",
            ),
            Port(
                name="from_tz",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 TIMEZONE_ID -> TEXT_GENERIC
                description="From Timezone",
            ),
            Port(
                name="to_tz",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 TIMEZONE_ID -> TEXT_GENERIC
                description="To Timezone",
            ),
        ],
        "outputs": [
            Port(
                name="iso",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 TIMESTAMP_ISO -> TEXT_GENERIC
                description="Converted ISO Timestamp",
            )
        ],
    },
    {
        "id_template": "checksum_crc32",
        "name": "CRC32 Checksum",
        "description": "CRC32 over hex bytes.",
        "inputs": [
            Port(name="hex", type=InterfaceType.HEX_STRING, description="Hex data"),
        ],
        "outputs": [
            Port(name="hex", type=InterfaceType.HEX_STRING, description="CRC32 Hex"),
            Port(name="int", type=InterfaceType.BIG_INT, description="CRC32 Int"),
        ],
    },
    # {
    #     "id_template": "geo_haversine",
    #     "name": "Haversine Distance",
    #     "description": "Great-circle distance (meters).",
    #     "inputs": [
    #         # Port(name="lat1", type=InterfaceType.LAT_LON, description="Lat 1"),
    #         # Port(name="lon1", type=InterfaceType.LAT_LON, description="Lon 1"),
    #         # Port(name="lat2", type=InterfaceType.LAT_LON, description="Lat 2"),
    #         # Port(name="lon2", type=InterfaceType.LAT_LON, description="Lon 2")
    #         Port(
    #             name="lat1",
    #             type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
    #             description="Lat 1",
    #         ),
    #         Port(
    #             name="lon1",
    #             type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
    #             description="Lon 1",
    #         ),
    #         Port(
    #             name="lat2",
    #             type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
    #             description="Lat 2",
    #         ),
    #         Port(
    #             name="lon2",
    #             type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
    #             description="Lon 2",
    #         ),
    #     ],
    #     "outputs": [
    #         Port(name="meters", type=InterfaceType.BIG_INT, description="Distance in meters"),
    #     ],
    # },
    # {
    #     "id_template": "otp_totp_generate",
    #     "name": "TOTP Generator",
    #     "description": "TOTP (RFC 6238) code by base32 secret & timestamp.",
    #     "inputs": [
    #         # Port(name="base32_secret", type=InterfaceType.BASE32_SECRET, description="Base32 Secret"),
    #         Port(
    #             name="base32_secret",
    #             type=InterfaceType.TEXT_GENERIC,  # 修改: 原 TEXT_BASE32_SECRET -> TEXT_GENERIC，避免孤立类型
    #             description="Base32 Secret",
    #         ),
    #         Port(
    #             name="timestamp_iso",
    #             type=InterfaceType.TEXT_GENERIC,  # 修改: 原 TIMESTAMP_ISO -> TEXT_GENERIC
    #             description="Timestamp",
    #         ),
    #         Port(name="step", type=InterfaceType.BIG_INT, description="Step (default 30)"),
    #         Port(name="digits", type=InterfaceType.BIG_INT, description="Digits (default 6)"),
    #         Port(
    #             name="algo",
    #             type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
    #             description="Algo (SHA1/256/512)",
    #         ),
    #     ],
    #     "outputs": [
    #         Port(
    #             name="code",
    #             type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
    #             description="TOTP Code",
    #         )
    #     ],
    # },
    {
        "id_template": "unicode_norm",
        "name": "Unicode Normalizer",
        "description": "Unicode normalize (NFC/NFD/NFKC/NFKD).",
        "inputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Text",
            ),
            Port(
                name="form",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Form",
            ),
        ],
        "outputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Normalized text",
            )
        ],
    },
    {
        "id_template": "text_bidi_sanitize",
        "name": "Bidi Sanitizer",
        "description": "Strip bidi control chars.",
        "inputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Text",
            )
        ],
        "outputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Sanitized text",
            )
        ],
    },
    {
        "id_template": "text_xor_hex",
        "name": "Hex XOR",
        "description": "XOR two hex strings.",
        "inputs": [
            Port(name="hex_a", type=InterfaceType.HEX_STRING, description="Hex A"),
            Port(name="hex_b", type=InterfaceType.HEX_STRING, description="Hex B"),
        ],
        "outputs": [
            Port(name="hex", type=InterfaceType.HEX_STRING, description="XOR Result Hex"),
        ],
    },
    {
        "id_template": "text_rotN",
        "name": "ROT-N Cipher",
        "description": "Caesar shift by N.",
        "inputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Text",
            ),
            Port(name="n", type=InterfaceType.BIG_INT, description="Shift N"),
        ],
        "outputs": [
            Port(
                name="text",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Rotated text",
            )
        ],
    },
    {
        "id_template": "luhn_check",
        "name": "Luhn Checker",
        "description": "Luhn validity of number string.",
        "inputs": [
            Port(
                name="number",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Number string",
            )
        ],
        "outputs": [
            Port(
                name="valid",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="True/False string",
            )
        ],
    },
    {
        "id_template": "iban_validate",
        "name": "IBAN Validator",
        "description": "IBAN checksum validation.",
        "inputs": [
            Port(
                name="iban",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="IBAN string",
            )
        ],
        "outputs": [
            Port(
                name="valid",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="True/False string",
            )
        ],
    },
    # --- 新增：主动掉落工具 (Tool -> Item) ---
    {
        "id_template": "matter_synthesizer",
        "name": "Matter Synthesizer",
        "description": "Synthesizes physical objects from data blueprints.",
        "inputs": [
            Port(
                name="blueprint",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC
                description="Object Blueprint",
            )
        ],
        "outputs": [
            # 输出类型为 Item，用于连接到物品的 Item 输入端口
            Port(name="output_slot", type=InterfaceType.ITEM, description="Synthesized Object"),
        ],
    },
]

# 物品模板库 (基础源头物品)
ITEM_TEMPLATES = [
    # 被动掉落物品 (只能放在容器内)
    {
        "id_template": "item_1",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="container", type=InterfaceType.HIDDEN_ITEM, description="Inside"),
        ],
        "outputs": [
            Port(name="content", type=InterfaceType.BIG_INT, description="The number"),
        ],
    },
    {
        "id_template": "item_2",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="container", type=InterfaceType.HIDDEN_ITEM, description="Inside"),
        ],
        "outputs": [
            Port(
                name="content",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 STRING -> TEXT_GENERIC，通用文本物品
                description="The text",
            )
        ],
    },
    {
        "id_template": "item_3",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="container", type=InterfaceType.HIDDEN_ITEM, description="Inside"),
        ],
        "outputs": [
            Port(name="content", type=InterfaceType.HEX_STRING, description="The hex code"),
        ],
    },
    {
        "id_template": "item_4",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="container", type=InterfaceType.HIDDEN_ITEM, description="Inside"),
        ],
        "outputs": [
            Port(
                name="content",
                type=InterfaceType.FILE_ID,  # 修改: 原 FILE_PATH_ZIP -> FILE_ID，统一文件 ID
                description="Zip file path",
            )
        ],
    },
    {
        "id_template": "item_5",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="container", type=InterfaceType.HIDDEN_ITEM, description="Inside"),
        ],
        "outputs": [
            Port(name="content", type=InterfaceType.HEX_STRING_KEY_AES, description="AES Key"),
        ],
    },
    {
        "id_template": "item_6",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="container", type=InterfaceType.HIDDEN_ITEM, description="Inside"),
        ],
        "outputs": [
            Port(name="content", type=InterfaceType.HEX_STRING_IV_AES, description="AES IV"),
        ],
    },
    {
        "id_template": "item_7",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="source_tool", type=InterfaceType.HIDDEN_ITEM, description="Produced by"),
        ],
        "outputs": [
            Port(name="content", type=InterfaceType.CODE_PYTHON, description="The integer"),
        ],
    },
    {
        "id_template": "item_8",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="source_tool", type=InterfaceType.HIDDEN_ITEM, description="Produced by"),
        ],
        "outputs": [
            Port(name="content", type=InterfaceType.HIDDEN_ITEM, description="The integer"),
        ],
    },
    {
        "id_template": "item_9",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="container", type=InterfaceType.ITEM, description="Inside"),
        ],
        "outputs": [
            Port(
                name="content",
                type=InterfaceType.FILE_ID,  # 修改: 原 FILE_PATH_JSON -> FILE_ID
                description="JSON file path",
            )
        ],
    },
    # 主动掉落物品 (可以被工具直接生产)
    {
        "id_template": "item_10",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="source_tool", type=InterfaceType.ITEM, description="Produced by"),
        ],
        "outputs": [
            Port(name="content", type=InterfaceType.BIG_INT, description="The number"),
        ],
    },
    {
        "id_template": "item_11",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="source_tool", type=InterfaceType.ITEM, description="Produced by"),
        ],
        "outputs": [
            Port(
                name="content",
                type=InterfaceType.CODE_PYTHON,  # 修改: 原 TEXT_GENERIC / STRING -> CODE_PYTHON，作为代码物品源头，专供 code_py_exec 使用
                description="Python code",
            )
        ],
    },
    {
        "id_template": "item_12",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="source_tool", type=InterfaceType.ITEM, description="Produced by"),
        ],
        "outputs": [
            Port(name="content", type=InterfaceType.HEX_STRING, description="The hex code"),
        ],
    },
    {
        "id_template": "item_13",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="source_tool", type=InterfaceType.ITEM, description="Produced by"),
        ],
        "outputs": [
            Port(name="content", type=InterfaceType.HEX_STRING_KEY_AES, description="AES Key"),
        ],
    },
    {
        "id_template": "item_14",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="source_tool", type=InterfaceType.ITEM, description="Produced by"),
        ],
        "outputs": [
            Port(name="content", type=InterfaceType.HEX_STRING_IV_AES, description="AES IV"),
        ],
    },
    {
        "id_template": "item_15",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="source_tool", type=InterfaceType.ITEM, description="Produced by"),
        ],
        "outputs": [
            Port(
                name="content",
                type=InterfaceType.TEXT_GENERIC,  # 修改: 原 TIMEZONE_ID -> TEXT_GENERIC，避免引入少量使用的时间/时区类型
                description="Timezone text",
            )
        ],
    },
    {
        "id_template": "item_16",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="source_tool", type=InterfaceType.ITEM, description="Produced by"),
        ],
        "outputs": [
            Port(
                name="content",
                type=InterfaceType.HIDDEN_ITEM,  # 修改: 原 TIMEZONE_ID -> TEXT_GENERIC，避免引入少量使用的时间/时区类型
                description="Timezone text",
            )
        ],
    },
]

# 容器模板库 - 分为主动掉落和被动掉落版本
CONTAINER_TEMPLATES = [
    # 生物识别保险箱
    # 主动掉落版本 (可以被工具直接生产)
    {
        "id_template": "container_1",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="source_tool", type=InterfaceType.ITEM, description="Produced by"),
            # 数据输入
            # Port(name="fingerprint_input", type=InterfaceType.HEX_STRING_HASH_SHA256, description="Fingerprint Hash")
            Port(name="fingerprint_input", type=InterfaceType.HEX_STRING, description="Fingerprint Hash"),
        ],
        "outputs": [
            Port(name="inner_space", type=InterfaceType.ITEM, description="Contents"),
        ],
    },
    # 被动掉落版本 (只能放在容器内)
    {
        "id_template": "container_2",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="container", type=InterfaceType.HIDDEN_ITEM, description="Inside"),
            # 数据输入
            # Port(name="fingerprint_input", type=InterfaceType.HEX_STRING_HASH_SHA256, description="Fingerprint Hash")
            Port(name="fingerprint_input", type=InterfaceType.HEX_STRING, description="Fingerprint Hash"),
        ],
        "outputs": [
            Port(name="inner_space", type=InterfaceType.ITEM, description="Contents"),
        ],
    },
    {
        "id_template": "container_3",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="container", type=InterfaceType.HIDDEN_ITEM, description="Inside"),
            # 数据输入
            # Port(name="fingerprint_input", type=InterfaceType.HEX_STRING_HASH_SHA256, description="Fingerprint Hash")
            Port(name="fingerprint_input", type=InterfaceType.BIG_INT, description="Fingerprint Hash"),
        ],
        "outputs": [
            Port(name="inner_space", type=InterfaceType.ITEM, description="Contents"),
        ],
    },
    {
        "id_template": "container_4",
        "name": "",
        "description": "",
        "inputs": [
            Port(name="container", type=InterfaceType.HIDDEN_ITEM, description="Inside"),
            # 数据输入
            # Port(name="fingerprint_input", type=InterfaceType.HEX_STRING_HASH_SHA256, description="Fingerprint Hash")
            Port(name="fingerprint_input", type=InterfaceType.TEXT_GENERIC, description="Fingerprint Hash"),
        ],
        "outputs": [
            Port(name="inner_space", type=InterfaceType.ITEM, description="Contents"),
        ],
    # 抽屉 / 文件夹 模板目前注释掉，保持不变
    },
]

# 终端机模板 - 原始逻辑终端
TERMINAL_TEMPLATE = {
    "id_template": "terminal_1",
    "name": "",
    "description": "",
    "inputs": [
        Port(
            name="slot_a",
            type=InterfaceType.TEXT_GENERIC,
            description="Input Slot A",
        ),
        Port(name="slot_b", type=InterfaceType.BIG_INT, description="Input Slot B"),
    ],
    "outputs": [
        Port(
            name="text_output",
            type=InterfaceType.TEXT_GENERIC,
            description="Text output when only slot_a is provided",
        ),
        Port(name="hex_output", type=InterfaceType.HEX_STRING, description="Hex output when only slot_b is provided"),
        Port(name="item_dispenser", type=InterfaceType.ITEM, description="Item output when both slots are provided"),
    ],
    # 验证规则：定义正确的输入值（待填充）
    "validation_rules": {
        "slot_a": {
            "type": "exact_match",
            "correct_value": None,  # TODO: 填充正确的 slot_a 值
            "description": "Correct code for slot A",
        },
        "slot_b": {
            "type": "exact_match",
            "correct_value": None,  # TODO: 填充正确的 slot_b 值
            "description": "Correct code for slot B",
        },
    },
    # 输出值规则：定义输出值（待填充）
    "output_rules": {
        "text_output": {
            "type": "static",
            "value": None,  # TODO: 填充 text_output 的值
        },
        "hex_output": {
            "type": "static",
            "value": None,  # TODO: 填充 hex_output 的值
        },
    },
    # 逻辑规则：定义输入和输出的对应关系
    "logic_rules": {
        "cases": [
            {
                "match": {"slot_a": "correct", "slot_b": "not_provided"},
                "output": {"text_output": None},  # TODO: 填充输出值
                "active_outputs": ["text_output"],
            },
            {
                "match": {"slot_a": "incorrect", "slot_b": "not_provided"},
                "output": "slot_a is incorrect",
            },
            {
                "match": {"slot_a": "not_provided", "slot_b": "correct"},
                "output": {"hex_output": None},  # TODO: 填充输出值
                "active_outputs": ["hex_output"],
            },
            {
                "match": {"slot_a": "not_provided", "slot_b": "incorrect"},
                "output": "slot_b is incorrect",
            },
            {
                "match": {"slot_a": "correct", "slot_b": "correct"},
                "output": {
                    "text_output": None,  # TODO: 填充输出值
                    "hex_output": None,  # TODO: 填充输出值
                },
                "active_outputs": ["item_dispenser"],
                "trigger_drop": True,
            },
            {
                "match": {"slot_a": "correct", "slot_b": "incorrect"},
                "output": "slot_b is incorrect",
            },
            {
                "match": {"slot_a": "incorrect", "slot_b": "correct"},
                "output": "slot_a is incorrect",
            },
        ]
    },
}

# 终端机模板 - 数学运算终端
MATH_TERMINAL_TEMPLATE = {
    "id_template": "terminal_2",
    "name": "",
    "description": "",
    "inputs": [
        Port(name="num1", type=InterfaceType.BIG_INT, description="First Number"),
        Port(name="num2", type=InterfaceType.BIG_INT, description="Second Number"),
    ],
    "outputs": [
        Port(
            name="text_result",
            type=InterfaceType.TEXT_GENERIC,
            description="Text result for partial input",
        ),
        Port(name="hex_result", type=InterfaceType.HEX_STRING, description="Hexadecimal result when both inputs provided"),
        Port(name="math_token", type=InterfaceType.ITEM, description="Mathematics token when both inputs provided"),
    ],
    # 验证规则：定义正确的输入值（待填充）
    "validation_rules": {
        "num1": {
            "type": "exact_match",
            "correct_value": None,  # TODO: 填充正确的 num1 值
            "description": "Correct value for num1",
        },
        "num2": {
            "type": "exact_match",
            "correct_value": None,  # TODO: 填充正确的 num2 值
            "description": "Correct value for num2",
        },
    },
    # 输出值规则：定义输出值（待填充）
    "output_rules": {
        "text_result": {
            "type": "static",
            "value": None,  # TODO: 填充 text_result 的值
        },
        "hex_result": {
            "type": "static",
            "value": None,  # TODO: 填充 hex_result 的值
        },
    },
    # 逻辑规则：定义输入和输出的对应关系
    "logic_rules": {
        "cases": [
            {
                "match": {"num1": "correct", "num2": "not_provided"},
                "output": {"text_result": None},  # TODO: 填充输出值
                "active_outputs": ["text_result"],
            },
            {
                "match": {"num1": "incorrect", "num2": "not_provided"},
                "output": "num1 is incorrect",
            },
            {
                "match": {"num1": "not_provided", "num2": "correct"},
                "output": {"text_result": None},  # TODO: 填充输出值
                "active_outputs": ["text_result"],
            },
            {
                "match": {"num1": "not_provided", "num2": "incorrect"},
                "output": "num2 is incorrect",
            },
            {
                "match": {"num1": "correct", "num2": "correct"},
                "output": {
                    "text_result": None,  # TODO: 填充输出值
                    "hex_result": None,  # TODO: 填充输出值
                },
                "active_outputs": ["hex_result", "math_token"],
                "trigger_drop": True,
            },
            {
                "match": {"num1": "correct", "num2": "incorrect"},
                "output": "num2 is incorrect",
            },
            {
                "match": {"num1": "incorrect", "num2": "correct"},
                "output": "num1 is incorrect",
            },
        ]
    },
}

# 终端机模板 - 加密解密终端
# CRYPT_TERMINAL_TEMPLATE = {
#     "id_template": "terminal_3",
#     "name": "",
#     "description": "",
#     "inputs": [
#         Port(
#             name="plaintext",
#             type=InterfaceType.TEXT_GENERIC,
#             description="Text Input",
#         ),
#         Port(name="key", type=InterfaceType.BIG_INT, description="Encryption Key"),
#     ],
#     "outputs": [
#         Port(
#             name="status",
#             type=InterfaceType.TEXT_GENERIC,
#             description="Status message for partial or complete input",
#         ),
#         Port(name="encrypted_hex", type=InterfaceType.HEX_STRING, description="Encrypted data when both inputs provided"),
#         Port(name="encryption_chip", type=InterfaceType.ITEM, description="Encryption chip when both inputs provided"),
#     ],
#     # 验证规则：定义正确的输入值（待填充）
#     "validation_rules": {
#         "plaintext": {
#             "type": "exact_match",
#             "correct_value": None,  # TODO: 填充正确的 plaintext 值
#             "description": "Correct plaintext for encryption",
#         },
#         "key": {
#             "type": "exact_match",
#             "correct_value": None,  # TODO: 填充正确的 key 值
#             "description": "Correct encryption key",
#         },
#     },
#     # 输出值规则：定义输出值（待填充）
#     "output_rules": {
#         "status": {
#             "type": "static",
#             "value": None,  # TODO: 填充 status 的值
#         },
#         "encrypted_hex": {
#             "type": "static",
#             "value": None,  # TODO: 填充 encrypted_hex 的值
#         },
#     },
#     # 逻辑规则：定义输入和输出的对应关系
#     "logic_rules": {
#         "cases": [
#             {
#                 "match": {"plaintext": "correct", "key": "not_provided"},
#                 "output": {"status": None},  # TODO: 填充输出值
#                 "active_outputs": ["status"],
#             },
#             {
#                 "match": {"plaintext": "incorrect", "key": "not_provided"},
#                 "output": "plaintext is incorrect",
#             },
#             {
#                 "match": {"plaintext": "correct", "key": "correct"},
#                 "output": {
#                     "status": None,  # TODO: 填充输出值
#                     "encrypted_hex": None,  # TODO: 填充输出值
#                 },
#                 "active_outputs": ["encrypted_hex", "encryption_chip"],
#                 "trigger_drop": True,
#             },
#             {
#                 "match": {"plaintext": "correct", "key": "incorrect"},
#                 "output": "key is incorrect",
#             },
#             {
#                 "match": {"plaintext": "incorrect", "key": "correct"},
#                 "output": "plaintext is incorrect",
#             },
#         ]
#     },
# }


# # 终端机模板 - 序列验证终端
# SEQUENCE_TERMINAL_TEMPLATE = {
#     "id_template": "terminal_4",
#     "name": "",
#     "description": "",
#     "inputs": [
#         Port(
#             name="sequence",
#             type=InterfaceType.TEXT_GENERIC,
#             description="Sequence Input",
#         ),
#         Port(name="checksum", type=InterfaceType.BIG_INT, description="Checksum Value"),
#     ],
#     "outputs": [
#         Port(
#             name="verification",
#             type=InterfaceType.TEXT_GENERIC,
#             description="Verification status message",
#         ),
#         Port(name="auth_code", type=InterfaceType.HEX_STRING, description="Authorization code when checksum valid"),
#         Port(name="access_card", type=InterfaceType.ITEM, description="Access card when checksum valid"),
#     ],
#     # 验证规则：定义正确的输入值（待填充）
#     "validation_rules": {
#         "sequence": {
#             "type": "exact_match",
#             "correct_value": None,  # TODO: 填充正确的 sequence 值
#             "description": "Correct sequence",
#         },
#         "checksum": {
#             "type": "exact_match",
#             "correct_value": None,  # TODO: 填充正确的 checksum 值
#             "description": "Correct checksum",
#         },
#     },
#     # 输出值规则：定义输出值（待填充）
#     "output_rules": {
#         "verification": {
#             "type": "static",
#             "value": None,  # TODO: 填充 verification 的值
#         },
#         "auth_code": {
#             "type": "static",
#             "value": None,  # TODO: 填充 auth_code 的值
#         },
#     },
#     # 逻辑规则：定义输入和输出的对应关系
#     "logic_rules": {
#         "cases": [
#             {
#                 "match": {"sequence": "correct", "checksum": "not_provided"},
#                 "output": {"verification": None},  # TODO: 填充输出值
#                 "active_outputs": ["verification"],
#             },
#             {
#                 "match": {"sequence": "incorrect", "checksum": "not_provided"},
#                 "output": "sequence is incorrect",
#             },
#             {
#                 "match": {"sequence": "correct", "checksum": "correct"},
#                 "output": {
#                     "verification": None,  # TODO: 填充输出值
#                     "auth_code": None,  # TODO: 填充输出值
#                 },
#                 "active_outputs": ["auth_code", "access_card"],
#                 "trigger_drop": True,
#             },
#             {
#                 "match": {"sequence": "correct", "checksum": "incorrect"},
#                 "output": {"verification": None},  # TODO: 填充输出值
#                 "active_outputs": ["verification"],
#             },
#             {
#                 "match": {"sequence": "incorrect", "checksum": "correct"},
#                 "output": "sequence is incorrect",
#             },
#         ]
#     },
# }

# 所有终端机模板的列表 - 便于统一管理和使用
TERMINAL_TEMPLATES = [
    TERMINAL_TEMPLATE,
    MATH_TERMINAL_TEMPLATE,
    # CRYPT_TERMINAL_TEMPLATE,
    # SEQUENCE_TERMINAL_TEMPLATE,
]


# ==================== 可掉落工具模板生成 ====================

def generate_droppable_tool_variants():
    """
    为所有工具模板自动生成可掉落版本
    
    为每个工具模板生成两个衍生版本：
    1. ITEM 触发版本：添加 ITEM 类型的输入端口
    2. HIDDEN_ITEM 触发版本：添加 HIDDEN_ITEM 类型的输入端口
    
    这些触发端口仅用于实现掉落机制，不参与工具的实际执行。
    被测模型在 investigate 工具时看不到这些触发端口。
    
    Returns:
        List[Dict]: 所有衍生工具模板的列表
    """
    droppable_variants = []
    
    # 为所有普通工具模板生成衍生版本
    for tmpl in TOOL_TEMPLATES:
        # 创建 ITEM 触发版本
        item_variant = tmpl.copy()
        # 保持 id_template 不变，因为 simulator 需要用它查找工具函数实现
        # 在原有inputs前面添加触发端口
        item_variant["inputs"] = [
            Port(
                name="trigger_item", 
                type=InterfaceType.ITEM, 
                description="Required item to unlock this tool"
            )
        ] + list(tmpl["inputs"])
        droppable_variants.append(item_variant)
        
        # 创建 HIDDEN_ITEM 触发版本
        hidden_variant = tmpl.copy()
        # 保持 id_template 不变，因为 simulator 需要用它查找工具函数实现
        # 在原有inputs前面添加触发端口
        hidden_variant["inputs"] = [
            Port(
                name="trigger_hidden", 
                type=InterfaceType.HIDDEN_ITEM, 
                description="Hidden item required to unlock this tool"
            )
        ] + list(tmpl["inputs"])
        droppable_variants.append(hidden_variant)
    
    # 为所有终端机模板生成衍生版本
    for tmpl in TERMINAL_TEMPLATES:
        # 创建 ITEM 触发版本
        item_variant = tmpl.copy()
        # 保持 id_template 不变，因为 simulator 需要用它查找工具函数实现
        item_variant["inputs"] = [
            Port(
                name="trigger_item", 
                type=InterfaceType.ITEM, 
                description="Required item to unlock this terminal"
            )
        ] + list(tmpl["inputs"])
        droppable_variants.append(item_variant)
        
        # 创建 HIDDEN_ITEM 触发版本
        hidden_variant = tmpl.copy()
        # 保持 id_template 不变，因为 simulator 需要用它查找工具函数实现
        hidden_variant["inputs"] = [
            Port(
                name="trigger_hidden", 
                type=InterfaceType.HIDDEN_ITEM, 
                description="Hidden item required to unlock this terminal"
            )
        ] + list(tmpl["inputs"])
        droppable_variants.append(hidden_variant)
    
    return droppable_variants


# 生成所有可掉落工具模板
DROPPABLE_TOOL_TEMPLATES = generate_droppable_tool_variants()

# 合并所有工具模板供 DAG 生成器使用
# 包含：原版工具 + 原版终端机 + 所有衍生版本
ALL_TOOL_TEMPLATES = TOOL_TEMPLATES + TERMINAL_TEMPLATES + DROPPABLE_TOOL_TEMPLATES

print(f"✓ 模板统计:")
print(f"  - 普通工具模板: {len(TOOL_TEMPLATES)} 个")
print(f"  - 终端机模板: {len(TERMINAL_TEMPLATES)} 个")
print(f"  - 可掉落衍生模板: {len(DROPPABLE_TOOL_TEMPLATES)} 个")
print(f"  - 总计: {len(ALL_TOOL_TEMPLATES)} 个工具模板")
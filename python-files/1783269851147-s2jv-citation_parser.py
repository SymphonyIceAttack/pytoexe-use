import sys
import json
import anystyle

def parse_citation_text(raw_text):
    try:
        parsed_result = anystyle.parse(raw_text)
        if parsed_result:
            return json.dumps(parsed_result[0], ensure_ascii=False)
        else:
            return json.dumps({"error": "�������Ϊ��"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

if __name__ == "__main__":
    # ���볤פģʽ�����ж�ȡ��׼����
    for line in sys.stdin:
        raw_text = line.strip()
        if not raw_text: 
            continue
        # ��������ӡ�����Delphi �Ĺܵ��Ჶ����� print��
        result_json = parse_citation_text(raw_text)
        print(result_json)
        # ǿ��ˢ�»�������ȷ�� Delphi �������յ�����
        sys.stdout.flush() 
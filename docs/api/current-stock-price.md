# 한국투자증권 Open API - 주식 현재가 시세 가이드

## 기본 정보

| 항목 | 내용 |
|------|------|
| API 통신방식 | REST |
| 메뉴 위치 | [국내주식] 기본시세 |
| API 명 | 주식현재가 시세 |
| API ID | v1_국내주식-008 |
| 실전 TR_ID | FHKST01010100 |
| 모의 TR_ID | FHKST01010100 |
| HTTP Method | GET |

## 엔드포인트

### 실전 환경
- **Domain**: `https://openapi.koreainvestment.com:9443`
- **URL**: `/uapi/domestic-stock/v1/quotations/inquire-price`

### 모의 환경
- **Domain**: `https://openapivts.koreainvestment.com:29443`
- **URL**: `/uapi/domestic-stock/v1/quotations/inquire-price`

## 개요

주식 현재가 시세 API입니다. 

**실시간 시세를 원하신다면 웹소켓 API를 활용하세요.**

※ 종목코드 마스터파일 파이썬 정제코드는 한국투자증권 Github 참고:
https://github.com/koreainvestment/open-trading-api/tree/main/stocks_info

## Request

### Request Header

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| content-type | 컨텐츠타입 | string | Y | 40 | `application/json; charset=utf-8` |
| authorization | 접근토큰 | string | Y | 350 | Bearer {access_token} |
| appkey | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey<br/>**⚠️ 절대 노출되지 않도록 주의** |
| appsecret | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret<br/>**⚠️ 절대 노출되지 않도록 주의** |
| personalseckey | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| tr_id | 거래ID | string | Y | 13 | `FHKST01010100` |
| tr_cont | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| custtype | 고객 타입 | string | Y | 1 | `B`: 법인, `P`: 개인 |
| seq_no | 일련번호 | string | N | 2 | [법인 필수] `001` |
| mac_address | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| phone_number | 핸드폰번호 | string | N | 12 | [법인 필수] 하이픈 제거 (예: 01011112222) |
| ip_addr | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| gt_uid | Global UID | string | N | 32 | [법인 전용] 거래고유번호 (거래별로 UNIQUE) |

### Request Query Parameters

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| FID_COND_MRKT_DIV_CODE | 조건 시장 분류 코드 | string | Y | 2 | `J`: KRX<br/>`NX`: NXT<br/>`UN`: 통합 |
| FID_INPUT_ISCD | 입력 종목코드 | string | Y | 12 | 종목코드 (예: 005930 삼성전자)<br/>**ETN은 종목코드 6자리 앞에 Q 입력 필수** |

### Request Example (Python)

```python
import requests

# 접근 토큰은 미리 발급받았다고 가정
access_token = "your_access_token"
appkey = "your_appkey"
appsecret = "your_appsecret"

url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-price"

headers = {
    "content-type": "application/json; charset=utf-8",
    "authorization": f"Bearer {access_token}",
    "appkey": appkey,
    "appsecret": appsecret,
    "tr_id": "FHKST01010100",
    "custtype": "P"  # 개인
}

params = {
    "fid_cond_mrkt_div_code": "J",    # KRX
    "fid_input_iscd": "005930"        # 삼성전자
}

response = requests.get(url, headers=headers, params=params)
data = response.json()
```

## Response

### Response Header

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| content-type | 컨텐츠타입 | string | Y | 40 | `application/json; charset=utf-8` |
| tr_id | 거래ID | string | Y | 13 | 요청한 tr_id |
| tr_cont | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| gt_uid | Global UID | string | N | 32 | [법인 전용] 거래고유번호 |

### Response Body

#### 공통 응답 필드

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| rt_cd | 성공 실패 여부 | string | Y | 1 | 0: 성공, 그 외: 실패 |
| msg_cd | 응답코드 | string | Y | 8 | 응답 메시지 코드 |
| msg1 | 응답메세지 | string | Y | 80 | 응답 메시지 |

#### output (종목 상세 정보)

**종목 상태 및 시장 정보**

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| iscd_stat_cls_code | 종목 상태 구분 코드 | string | 51: 관리종목, 52: 투자위험, 53: 투자경고<br/>54: 투자주의, 55: 신용가능, 57: 증거금100%<br/>58: 거래정지, 59: 단기과열종목 |
| marg_rate | 증거금 비율 | string | |
| rprs_mrkt_kor_name | 대표 시장 한글 명 | string | |
| bstp_kor_isnm | 업종 한글 종목명 | string | |
| temp_stop_yn | 임시 정지 여부 | string | Y/N |
| oprc_rang_cont_yn | 시가 범위 연장 여부 | string | Y/N |
| clpr_rang_cont_yn | 종가 범위 연장 여부 | string | Y/N |
| crdt_able_yn | 신용 가능 여부 | string | Y/N |
| grmn_rate_cls_code | 보증금 비율 구분 코드 | string | |
| elw_pblc_yn | ELW 발행 여부 | string | Y/N |
| mang_issu_cls_code | 관리종목여부 | string | |
| mrkt_warn_cls_code | 시장경고코드 | string | |
| short_over_yn | 단기과열여부 | string | Y/N |
| sltr_yn | 정리매매여부 | string | Y/N |
| invt_caful_yn | 투자유의여부 | string | Y/N |

**현재가 및 등락 정보**

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| stck_prpr | 주식 현재가 | string | |
| prdy_vrss | 전일 대비 | string | |
| prdy_vrss_sign | 전일 대비 부호 | string | |
| prdy_ctrt | 전일 대비율 | string | |
| acml_tr_pbmn | 누적 거래 대금 | string | |
| acml_vol | 누적 거래량 | string | |
| prdy_vrss_vol_rate | 전일 대비 거래량 비율 | string | |

**가격 정보**

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| stck_oprc | 주식 시가 | string | |
| stck_hgpr | 주식 최고가 | string | |
| stck_lwpr | 주식 최저가 | string | |
| stck_mxpr | 주식 상한가 | string | |
| stck_llam | 주식 하한가 | string | |
| stck_sdpr | 주식 기준가 | string | |
| wghn_avrg_stck_prc | 가중 평균 주식 가격 | string | |
| stck_fcam | 주식 액면가 | string | |
| stck_sspr | 주식 대용가 | string | |
| aspr_unit | 호가단위 | string | |
| hts_deal_qty_unit_val | HTS 매매 수량 단위 값 | string | |
| rstc_wdth_prc | 제한 폭 가격 | string | |

**외국인 및 프로그램 정보**

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| hts_frgn_ehrt | HTS 외국인 소진율 | string | |
| frgn_ntby_qty | 외국인 순매수 수량 | string | |
| frgn_hldn_qty | 외국인 보유 수량 | string | |
| pgtr_ntby_qty | 프로그램매매 순매수 수량 | string | |

**피벗 지표**

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| pvt_scnd_dmrs_prc | 피벗 2차 디저항 가격 | string | |
| pvt_frst_dmrs_prc | 피벗 1차 디저항 가격 | string | |
| pvt_pont_val | 피벗 포인트 값 | string | |
| pvt_frst_dmsp_prc | 피벗 1차 디지지 가격 | string | |
| pvt_scnd_dmsp_prc | 피벗 2차 디지지 가격 | string | |
| dmrs_val | 디저항 값 | string | |
| dmsp_val | 디지지 값 | string | |

**재무 정보**

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| lstn_stcn | 상장 주수 | string | |
| hts_avls | HTS 시가총액 | string | |
| per | PER | string | |
| pbr | PBR | string | |
| eps | EPS | string | |
| bps | BPS | string | |
| stac_month | 결산 월 | string | |
| vol_tnrt | 거래량 회전율 | string | |
| cpfn | 자본금 | string | |
| cpfn_cnnm | 자본금 통화명 | string | |
| fcam_cnnm | 액면가 통화명 | string | |
| apprch_rate | 접근도 | string | |

**고가/저가 정보 (250일 기준)**

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| d250_hgpr | 250일 최고가 | string | |
| d250_hgpr_date | 250일 최고가 일자 | string | |
| d250_hgpr_vrss_prpr_rate | 250일 최고가 대비 현재가 비율 | string | |
| d250_lwpr | 250일 최저가 | string | |
| d250_lwpr_date | 250일 최저가 일자 | string | |
| d250_lwpr_vrss_prpr_rate | 250일 최저가 대비 현재가 비율 | string | |

**고가/저가 정보 (연중 기준)**

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| stck_dryy_hgpr | 주식 연중 최고가 | string | |
| dryy_hgpr_vrss_prpr_rate | 연중 최고가 대비 현재가 비율 | string | |
| dryy_hgpr_date | 연중 최고가 일자 | string | |
| stck_dryy_lwpr | 주식 연중 최저가 | string | |
| dryy_lwpr_vrss_prpr_rate | 연중 최저가 대비 현재가 비율 | string | |
| dryy_lwpr_date | 연중 최저가 일자 | string | |

**고가/저가 정보 (52주 기준)**

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| w52_hgpr | 52주일 최고가 | string | |
| w52_hgpr_vrss_prpr_ctrt | 52주일 최고가 대비 현재가 대비 | string | |
| w52_hgpr_date | 52주일 최고가 일자 | string | |
| w52_lwpr | 52주일 최저가 | string | |
| w52_lwpr_vrss_prpr_ctrt | 52주일 최저가 대비 현재가 대비 | string | |
| w52_lwpr_date | 52주일 최저가 일자 | string | |

**기타 정보**

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| whol_loan_rmnd_rate | 전체 융자 잔고 비율 | string | |
| ssts_yn | 공매도가능여부 | string | Y/N |
| stck_shrn_iscd | 주식 단축 종목코드 | string | |
| vi_cls_code | VI적용구분코드 | string | |
| ovtm_vi_cls_code | 시간외단일가VI적용구분코드 | string | |
| last_ssts_cntg_qty | 최종 공매도 체결 수량 | string | |
| new_hgpr_lwpr_cls_code | 신 고가 저가 구분 코드 | string | |

### Response Example

```json
{
  "output": {
    "iscd_stat_cls_code": "55",
    "marg_rate": "20.00",
    "rprs_mrkt_kor_name": "KOSPI200",
    "bstp_kor_isnm": "전기.전자",
    "temp_stop_yn": "N",
    "oprc_rang_cont_yn": "N",
    "clpr_rang_cont_yn": "N",
    "crdt_able_yn": "Y",
    "grmn_rate_cls_code": "40",
    "elw_pblc_yn": "Y",
    "stck_prpr": "128500",
    "prdy_vrss": "0",
    "prdy_vrss_sign": "3",
    "prdy_ctrt": "0.00",
    "acml_tr_pbmn": "344570137500",
    "acml_vol": "2669075",
    "prdy_vrss_vol_rate": "75.14",
    "stck_oprc": "128500",
    "stck_hgpr": "130000",
    "stck_lwpr": "128500",
    "stck_mxpr": "167000",
    "stck_llam": "90000",
    "stck_sdpr": "128500",
    "wghn_avrg_stck_prc": "129097.23",
    "hts_frgn_ehrt": "49.48",
    "frgn_ntby_qty": "0",
    "pgtr_ntby_qty": "287715",
    "pvt_scnd_dmrs_prc": "131833",
    "pvt_frst_dmrs_prc": "130166",
    "pvt_pont_val": "128333",
    "pvt_frst_dmsp_prc": "126666",
    "pvt_scnd_dmsp_prc": "124833",
    "dmrs_val": "129250",
    "dmsp_val": "125750",
    "cpfn": "36577",
    "rstc_wdth_prc": "38500",
    "stck_fcam": "5000",
    "stck_sspr": "97660",
    "aspr_unit": "500",
    "hts_deal_qty_unit_val": "1",
    "lstn_stcn": "728002365",
    "hts_avls": "935483",
    "per": "19.67",
    "pbr": "1.72",
    "stac_month": "12",
    "vol_tnrt": "0.37",
    "eps": "6532.00",
    "bps": "74721.00",
    "d250_hgpr": "149500",
    "d250_hgpr_date": "20210225",
    "d250_hgpr_vrss_prpr_rate": "-14.05",
    "d250_lwpr": "90500",
    "d250_lwpr_date": "20211013",
    "d250_lwpr_vrss_prpr_rate": "41.99",
    "stck_dryy_hgpr": "132500",
    "dryy_hgpr_vrss_prpr_rate": "-3.02",
    "dryy_hgpr_date": "20220103",
    "stck_dryy_lwpr": "121500",
    "dryy_lwpr_vrss_prpr_rate": "5.76",
    "dryy_lwpr_date": "20220105",
    "w52_hgpr": "149500",
    "w52_hgpr_vrss_prpr_ctrt": "-14.05",
    "w52_hgpr_date": "20210225",
    "w52_lwpr": "90500",
    "w52_lwpr_vrss_prpr_ctrt": "41.99",
    "w52_lwpr_date": "20211013",
    "whol_loan_rmnd_rate": "0.22",
    "ssts_yn": "Y",
    "stck_shrn_iscd": "000660",
    "fcam_cnnm": "5,000",
    "cpfn_cnnm": "36,576 억",
    "frgn_hldn_qty": "360220601",
    "vi_cls_code": "N",
    "ovtm_vi_cls_code": "N",
    "last_ssts_cntg_qty": "43916",
    "invt_caful_yn": "N",
    "mrkt_warn_cls_code": "00",
    "short_over_yn": "N",
    "sltr_yn": "N"
  },
  "rt_cd": "0",
  "msg_cd": "MCA00000",
  "msg1": "정상처리 되었습니다!"
}
```

## 사용 예시

### 기본 사용법

```python
import requests

class StockPriceAPI:
    def __init__(self, access_token, appkey, appsecret, is_real=True):
        self.access_token = access_token
        self.appkey = appkey
        self.appsecret = appsecret
        
        if is_real:
            self.base_url = "https://openapi.koreainvestment.com:9443"
        else:
            self.base_url = "https://openapivts.koreainvestment.com:29443"
    
    def get_current_price(self, stock_code, market='J'):
        """
        주식 현재가 조회
        
        Args:
            stock_code: 종목코드 (예: '005930')
            market: 시장구분 ('J': KRX, 'NX': NXT, 'UN': 통합)
        
        Returns:
            dict: API 응답 데이터
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "FHKST01010100",
            "custtype": "P"
        }
        
        params = {
            "fid_cond_mrkt_div_code": market,
            "fid_input_iscd": stock_code
        }
        
        response = requests.get(url, headers=headers, params=params)
        return response.json()

# 사용 예시
api = StockPriceAPI(access_token, appkey, appsecret, is_real=False)

# 삼성전자 현재가 조회
result = api.get_current_price('005930')

if result['rt_cd'] == '0':
    output = result['output']
    print(f"종목명: {output['bstp_kor_isnm']}")
    print(f"현재가: {output['stck_prpr']}")
    print(f"전일대비: {output['prdy_vrss']} ({output['prdy_ctrt']}%)")
    print(f"시가: {output['stck_oprc']}")
    print(f"고가: {output['stck_hgpr']}")
    print(f"저가: {output['stck_lwpr']}")
    print(f"거래량: {output['acml_vol']}")
    print(f"거래대금: {output['acml_tr_pbmn']}")
else:
    print(f"오류: {result['msg1']}")
```

### 여러 종목 조회

```python
def get_multiple_stocks_info(api, stock_codes):
    """여러 종목의 현재가 정보를 조회"""
    results = {}
    
    for code in stock_codes:
        try:
            data = api.get_current_price(code)
            if data['rt_cd'] == '0':
                output = data['output']
                results[code] = {
                    '현재가': int(output['stck_prpr']),
                    '전일대비': int(output['prdy_vrss']),
                    '등락률': float(output['prdy_ctrt']),
                    '거래량': int(output['acml_vol']),
                    'PER': float(output['per']) if output['per'] else 0,
                    'PBR': float(output['pbr']) if output['pbr'] else 0
                }
        except Exception as e:
            print(f"종목 {code} 조회 실패: {e}")
    
    return results

# 사용 예시
stock_codes = ['005930', '000660', '035420', '051910']  # 삼성전자, SK하이닉스, NAVER, LG화학
stocks_info = get_multiple_stocks_info(api, stock_codes)

for code, info in stocks_info.items():
    print(f"\n종목코드: {code}")
    for key, value in info.items():
        print(f"  {key}: {value}")
```

### 기술적 지표 활용

```python
def analyze_stock_position(api, stock_code):
    """종목의 기술적 위치 분석"""
    result = api.get_current_price(stock_code)
    
    if result['rt_cd'] != '0':
        return None
    
    output = result['output']
    current_price = float(output['stck_prpr'])
    
    # 52주 최고/최저 대비 현재 위치
    w52_high = float(output['w52_hgpr'])
    w52_low = float(output['w52_lwpr'])
    w52_position = ((current_price - w52_low) / (w52_high - w52_low)) * 100
    
    # 피벗 포인트 분석
    pivot = float(output['pvt_pont_val'])
    resistance1 = float(output['pvt_frst_dmrs_prc'])
    support1 = float(output['pvt_frst_dmsp_prc'])
    
    analysis = {
        '현재가': current_price,
        '52주_최고가': w52_high,
        '52주_최저가': w52_low,
        '52주_위치': f"{w52_position:.2f}%",
        '피벗포인트': pivot,
        '저항선1': resistance1,
        '지지선1': support1,
        '피벗대비': '상승' if current_price > pivot else '하락',
        '외국인소진율': output['hts_frgn_ehrt'] + '%'
    }
    
    return analysis

# 사용 예시
analysis = analyze_stock_position(api, '005930')
if analysis:
    print("=== 기술적 분석 ===")
    for key, value in analysis.items():
        print(f"{key}: {value}")
```

## 주의사항

1. **실시간 시세**: 이 API는 현재가 조회이며, 실시간 시세가 필요한 경우 웹소켓 API를 사용해야 합니다
2. **ETN 종목**: ETN 종목 조회 시에는 종목코드 6자리 앞에 'Q'를 붙여야 합니다
3. **데이터 정확성**: 시장 상황에 따라 일부 데이터가 0 또는 null일 수 있습니다
4. **호출 빈도**: API 호출 제한이 있으므로, 과도한 호출을 피해야 합니다
5. **종목코드**: 정확한 종목코드는 한국투자증권 Github의 종목코드 마스터파일을 참고하세요

## 응답 코드 참고

### 종목 상태 구분 코드 (iscd_stat_cls_code)

- `51`: 관리종목
- `52`: 투자위험
- `53`: 투자경고
- `54`: 투자주의
- `55`: 신용가능
- `57`: 증거금 100%
- `58`: 거래정지
- `59`: 단기과열종목

### 전일 대비 부호 (prdy_vrss_sign)

- `1` 또는 `2`: 상승
- `3`: 보합
- `4` 또는 `5`: 하락

## 활용 팁

1. **투자 판단**: PER, PBR, EPS, BPS 등 재무 지표를 활용하여 투자 가치 평가
2. **기술적 분석**: 피벗 포인트, 52주 고가/저가, 250일 고가/저가 등으로 기술적 위치 파악
3. **외국인 동향**: 외국인 순매수 수량과 보유 수량으로 외국인 투자 동향 분석
4. **시장 경고**: 종목 상태 코드, 시장경고코드 등으로 투자 위험 요인 확인
5. **공매도 정보**: 공매도 가능 여부와 체결 수량으로 공매도 동향 파악
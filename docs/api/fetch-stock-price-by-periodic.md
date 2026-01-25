# 한국투자증권 Open API - 국내주식 기간별 시세 가이드

## 기본 정보

| 항목 | 내용 |
|------|------|
| API 통신방식 | REST |
| 메뉴 위치 | [국내주식] 기본시세 |
| API 명 | 국내주식기간별시세(일_주_월_년) |
| API ID | v1_국내주식-016 |
| 실전 TR_ID | FHKST03010100 |
| 모의 TR_ID | FHKST03010100 |
| HTTP Method | GET |

## 엔드포인트

### 실전 환경
- **Domain**: `https://openapi.koreainvestment.com:9443`
- **URL**: `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice`

### 모의 환경
- **Domain**: `https://openapivts.koreainvestment.com:29443`
- **URL**: `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice`

## 개요

국내주식 기간별 시세(일/주/월/년) API입니다.

**실전계좌/모의계좌의 경우, 한 번의 호출에 최대 100건까지 확인 가능합니다.**

## Request

### Request Header

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| content-type | 컨텐츠타입 | string | Y | 40 | `application/json; charset=utf-8` |
| authorization | 접근토큰 | string | Y | 350 | Bearer {access_token}<br/>- 일반고객: Access token 유효기간 1일<br/>- 법인: Access token 유효기간 3개월, Refresh token 1년 |
| appkey | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey<br/>**⚠️ 절대 노출되지 않도록 주의** |
| appsecret | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret<br/>**⚠️ 절대 노출되지 않도록 주의** |
| personalseckey | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| tr_id | 거래ID | string | Y | 13 | `FHKST03010100` |
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
| FID_INPUT_ISCD | 입력 종목코드 | string | Y | 12 | 종목코드 (예: 005930 삼성전자) |
| FID_INPUT_DATE_1 | 입력 날짜 1 | string | Y | 10 | 조회 시작일자 (YYYYMMDD) |
| FID_INPUT_DATE_2 | 입력 날짜 2 | string | Y | 10 | 조회 종료일자 (YYYYMMDD)<br/>**최대 100개** |
| FID_PERIOD_DIV_CODE | 기간분류코드 | string | Y | 32 | `D`: 일봉<br/>`W`: 주봉<br/>`M`: 월봉<br/>`Y`: 년봉 |
| FID_ORG_ADJ_PRC | 수정주가 원주가 가격 여부 | string | Y | 10 | `0`: 수정주가<br/>`1`: 원주가 |

### Request Example (Python)

```python
import requests

# 접근 토큰은 미리 발급받았다고 가정
access_token = "your_access_token"
appkey = "your_appkey"
appsecret = "your_appsecret"

url = "https://openapi.koreainvestment.com:9943/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"

headers = {
    "content-type": "application/json; charset=utf-8",
    "authorization": f"Bearer {access_token}",
    "appkey": appkey,
    "appsecret": appsecret,
    "tr_id": "FHKST03010100",
    "custtype": "P"  # 개인
}

params = {
    "fid_cond_mrkt_div_code": "J",         # KRX
    "fid_input_iscd": "005930",            # 삼성전자
    "fid_input_date_1": "20240101",        # 시작일자
    "fid_input_date_2": "20240131",        # 종료일자
    "fid_period_div_code": "D",            # 일봉
    "fid_org_adj_prc": "0"                 # 수정주가
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

#### output1 (종목 현재 정보 - Single Object)

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| prdy_vrss | 전일 대비 | string | |
| prdy_vrss_sign | 전일 대비 부호 | string | |
| prdy_ctrt | 전일 대비율 | string | |
| stck_prdy_clpr | 주식 전일 종가 | string | |
| acml_vol | 누적 거래량 | string | |
| acml_tr_pbmn | 누적 거래 대금 | string | |
| hts_kor_isnm | HTS 한글 종목명 | string | |
| stck_prpr | 주식 현재가 | string | |
| stck_shrn_iscd | 주식 단축 종목코드 | string | |
| prdy_vol | 전일 거래량 | string | |
| stck_mxpr | 주식 상한가 | string | |
| stck_llam | 주식 하한가 | string | |
| stck_oprc | 주식 시가 | string | |
| stck_hgpr | 주식 최고가 | string | |
| stck_lwpr | 주식 최저가 | string | |
| stck_prdy_oprc | 주식 전일 시가 | string | |
| stck_prdy_hgpr | 주식 전일 최고가 | string | |
| stck_prdy_lwpr | 주식 전일 최저가 | string | |
| askp | 매도호가 | string | |
| bidp | 매수호가 | string | |
| prdy_vrss_vol | 전일 대비 거래량 | string | |
| vol_tnrt | 거래량 회전율 | string | 11(8.2) 형식 |
| stck_fcam | 주식 액면가 | string | |
| lstn_stcn | 상장 주수 | string | |
| cpfn | 자본금 | string | |
| hts_avls | HTS 시가총액 | string | |
| per | PER | string | 11(8.2) 형식 |
| eps | EPS | string | 14(11.2) 형식 |
| pbr | PBR | string | 11(8.2) 형식 |
| itewhol_loan_rmnd_ratem | 전체 융자 잔고 비율 | string | 13(8.4) 형식 |

#### output2 (기간별 시세 데이터 - Array)

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| stck_bsop_date | 주식 영업 일자 | string | YYYYMMDD |
| stck_clpr | 주식 종가 | string | |
| stck_oprc | 주식 시가 | string | |
| stck_hgpr | 주식 최고가 | string | |
| stck_lwpr | 주식 최저가 | string | |
| acml_vol | 누적 거래량 | string | |
| acml_tr_pbmn | 누적 거래 대금 | string | |
| flng_cls_code | 락 구분 코드 | string | 01: 권리락, 02: 배당락, 03: 분배락, 04: 권배락<br/>05: 중간(분기)배당락, 06: 권리중간배당락<br/>07: 권리분기배당락 |
| prtt_rate | 분할 비율 | string | 기준가/전일 종가 |
| mod_yn | 변경 여부 | string | 현재 영업일에 체결이 발생하지 않아<br/>시가가 없을 경우 Y로 표시 |
| prdy_vrss_sign | 전일 대비 부호 | string | |
| prdy_vrss | 전일 대비 | string | |
| revl_issu_reas | 재평가사유코드 | string | 00: 해당없음, 01: 회사분할, 02: 자본감소<br/>03: 장기간정지, 04: 초과분배, 05: 대규모배당<br/>06: 회사분할합병, 07: ETN증권병합/분할<br/>08: 신종증권기세조정, 99: 기타 |

### Response Example

```json
{
    "msg_cd": "MCA00000",
    "output1": {
        "acml_tr_pbmn": "236062833000",
        "acml_vol": "2106409",
        "askp": "112500",
        "bidp": "112000",
        "cpfn": "36577",
        "eps": "13190.00",
        "hts_avls": "815363",
        "hts_kor_isnm": "SK하이닉스",
        "itewhol_loan_rmnd_ratem": "0.32",
        "lstn_stcn": "728002365",
        "pbr": "1.26",
        "per": "8.49",
        "prdy_ctrt": "0.90",
        "prdy_vol": "3680049",
        "prdy_vrss": "1000",
        "prdy_vrss_sign": "2",
        "prdy_vrss_vol": "-1573640",
        "stck_fcam": "5000",
        "stck_hgpr": "113000",
        "stck_llam": "78000",
        "stck_lwpr": "111000",
        "stck_mxpr": "144000",
        "stck_oprc": "111500",
        "stck_prdy_clpr": "111000",
        "stck_prdy_hgpr": "112500",
        "stck_prdy_lwpr": "110000",
        "stck_prdy_oprc": "110500",
        "stck_prpr": "112000",
        "stck_shrn_iscd": "000660",
        "vol_tnrt": "0.29"
    },
    "output2": [
        {
            "acml_tr_pbmn": "237914727500",
            "acml_vol": "2203472",
            "flng_cls_code": "00",
            "mod_yn": "N",
            "prdy_vrss": "0",
            "prdy_vrss_sign": "3",
            "prtt_rate": "0.00",
            "revl_issu_reas": "",
            "stck_bsop_date": "20220509",
            "stck_clpr": "107500",
            "stck_hgpr": "109000",
            "stck_lwpr": "106500",
            "stck_oprc": "107000"
        }
    ]
}
```

## 사용 예시

### 기본 사용법

```python
import requests
from datetime import datetime, timedelta

class StockPriceAPI:
    def __init__(self, access_token, appkey, appsecret, is_real=True):
        self.access_token = access_token
        self.appkey = appkey
        self.appsecret = appsecret
        
        if is_real:
            self.base_url = "https://openapi.koreainvestment.com:9443"
        else:
            self.base_url = "https://openapivts.koreainvestment.com:29443"
    
    def get_daily_price(self, stock_code, start_date, end_date, 
                       period='D', adj_price=True, market='J'):
        """
        주식 기간별 시세 조회
        
        Args:
            stock_code: 종목코드 (예: '005930')
            start_date: 시작일자 (YYYYMMDD 또는 datetime)
            end_date: 종료일자 (YYYYMMDD 또는 datetime)
            period: 기간 ('D': 일, 'W': 주, 'M': 월, 'Y': 년)
            adj_price: 수정주가 여부 (True: 수정주가, False: 원주가)
            market: 시장구분 ('J': KRX, 'NX': NXT, 'UN': 통합)
        
        Returns:
            dict: API 응답 데이터
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        
        # datetime 객체를 문자열로 변환
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y%m%d')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y%m%d')
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "FHKST03010100",
            "custtype": "P"
        }
        
        params = {
            "fid_cond_mrkt_div_code": market,
            "fid_input_iscd": stock_code,
            "fid_input_date_1": start_date,
            "fid_input_date_2": end_date,
            "fid_period_div_code": period,
            "fid_org_adj_prc": "0" if adj_price else "1"
        }
        
        response = requests.get(url, headers=headers, params=params)
        return response.json()

# 사용 예시
api = StockPriceAPI(access_token, appkey, appsecret, is_real=False)

# 삼성전자 최근 1개월 일봉 데이터 조회
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

result = api.get_daily_price(
    stock_code='005930',
    start_date=start_date,
    end_date=end_date,
    period='D',
    adj_price=True
)

# 결과 처리
if result['rt_cd'] == '0':
    print(f"종목명: {result['output1']['hts_kor_isnm']}")
    print(f"현재가: {result['output1']['stck_prpr']}")
    print(f"전일대비: {result['output1']['prdy_vrss']} ({result['output1']['prdy_ctrt']}%)")
    
    print("\n일별 시세:")
    for item in result['output2']:
        print(f"{item['stck_bsop_date']}: "
              f"시가 {item['stck_oprc']}, "
              f"고가 {item['stck_hgpr']}, "
              f"저가 {item['stck_lwpr']}, "
              f"종가 {item['stck_clpr']}, "
              f"거래량 {item['acml_vol']}")
else:
    print(f"오류: {result['msg1']}")
```

### 데이터 분석 예시

```python
import pandas as pd

def price_data_to_dataframe(api_response):
    """API 응답을 pandas DataFrame으로 변환"""
    if api_response['rt_cd'] != '0':
        raise ValueError(f"API Error: {api_response['msg1']}")
    
    # output2 데이터를 DataFrame으로 변환
    df = pd.DataFrame(api_response['output2'])
    
    # 데이터 타입 변환
    df['stck_bsop_date'] = pd.to_datetime(df['stck_bsop_date'])
    
    numeric_columns = ['stck_clpr', 'stck_oprc', 'stck_hgpr', 
                      'stck_lwpr', 'acml_vol', 'acml_tr_pbmn']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col])
    
    # 날짜 기준 정렬
    df = df.sort_values('stck_bsop_date')
    
    # 컬럼명 변경 (선택사항)
    df = df.rename(columns={
        'stck_bsop_date': 'date',
        'stck_oprc': 'open',
        'stck_hgpr': 'high',
        'stck_lwpr': 'low',
        'stck_clpr': 'close',
        'acml_vol': 'volume'
    })
    
    return df

# 사용 예시
result = api.get_daily_price('005930', '20240101', '20240131')
df = price_data_to_dataframe(result)

# 기본 통계
print(df.describe())

# 이동평균 계산
df['MA5'] = df['close'].rolling(window=5).mean()
df['MA20'] = df['close'].rolling(window=20).mean()

# 변동성 계산
df['daily_return'] = df['close'].pct_change()
volatility = df['daily_return'].std()

print(f"일간 변동성: {volatility:.4f}")
```

## 주의사항

1. **최대 조회 건수**: 한 번의 호출에 최대 100건까지만 조회 가능
2. **연속 조회 불가**: 이 API는 `tr_cont`를 이용한 연속 조회를 지원하지 않음
3. **날짜 범위**: `FID_INPUT_DATE_1`(시작일)과 `FID_INPUT_DATE_2`(종료일) 사이의 데이터가 100건을 초과하지 않도록 주의
4. **수정주가**: 과거 데이터 분석 시에는 수정주가(`FID_ORG_ADJ_PRC=0`) 사용 권장
5. **기간 분류**: 
   - 일봉(D): 영업일 기준
   - 주봉(W): 주 단위 데이터
   - 월봉(M): 월 단위 데이터
   - 년봉(Y): 년 단위 데이터
6. **시장 휴장일**: 주말, 공휴일 등 시장 휴장일 데이터는 포함되지 않음

## 응답 코드 참고

### 전일 대비 부호 (prdy_vrss_sign)

- `1` 또는 `2`: 상승
- `3`: 보합
- `4` 또는 `5`: 하락

### 락 구분 코드 (flng_cls_code)

- `00`: 해당없음
- `01`: 권리락
- `02`: 배당락
- `03`: 분배락
- `04`: 권배락
- `05`: 중간(분기)배당락
- `06`: 권리중간배당락
- `07`: 권리분기배당락
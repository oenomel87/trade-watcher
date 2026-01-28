# 한국투자증권 Open API - 해외주식 종목/지수/환율 기간별 시세 가이드

## 기본 정보

| 항목 | 내용 |
|------|------|
| API 통신방식 | REST |
| 메뉴 위치 | [해외주식] 기본시세 |
| API 명 | 해외주식 종목/지수/환율 기간별 시세 |
| API ID | v1_해외주식-012 |
| 실전 TR_ID | FHKST03030100 |
| 모의 TR_ID | FHKST03030100 |
| HTTP Method | GET |

## 엔드포인트

### 실전 환경
- **Domain**: `https://openapi.koreainvestment.com:9443`
- **URL**: `/uapi/overseas-price/v1/quotations/inquire-daily-chartprice`

### 모의 환경
- **Domain**: `https://openapivts.koreainvestment.com:29443`
- **URL**: `/uapi/overseas-price/v1/quotations/inquire-daily-chartprice`

## 개요

해외주식 종목, 해외지수, 환율, 국채, 금선물의 기간별(일/주/월/년) 시세를 조회하는 API입니다.

### 주의사항
- **미국 주식 조회 시**: 다우30, 나스닥100, S&P500 종목만 조회 가능합니다. 더 많은 종목 시세가 필요한 경우 '해외주식기간별시세' API를 사용하십시오.
- **해외지수**: 당일 시세의 경우 지연 시세 또는 종가 시세가 제공됩니다.

## Request

### Request Header

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| content-type | 컨텐츠타입 | string | N | 40 | `application/json; charset=utf-8` |
| authorization | 접근토큰 | string | Y | 350 | Bearer {access_token} |
| appkey | 앱키 | string | Y | 36 | 발급받은 appkey |
| appsecret | 앱시크릿키 | string | Y | 180 | 발급받은 appsecret |
| tr_id | 거래ID | string | Y | 13 | `FHKST03030100` |
| tr_cont | 연속 거래 여부 | string | N | 1 | |
| custtype | 고객 타입 | string | N | 1 | `B`: 법인, `P`: 개인 |
| seq_no | 일련번호 | string | N | 2 | [법인 필수] `001` |
| mac_address | 맥주소 | string | N | 12 | Mac address 값 |
| phone_number | 핸드폰번호 | string | N | 12 | [법인 필수] 하이픈 제거 |
| ip_addr | 접속 단말 공인 IP | string | N | 12 | [법인 필수] IP Address |
| gt_uid | Global UID | string | N | 32 | [법인 전용] 거래고유번호 |

### Request Query Parameters

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| FID_COND_MRKT_DIV_CODE | 조건 시장 분류 코드 | string | Y | 2 | `N`: 해외지수, `X`: 환율, `I`: 국채, `S`: 금선물 |
| FID_INPUT_ISCD | 입력 종목코드 | string | Y | 12 | 종목코드 (예: `.DJI`, `.NAS`, `.IXIC`) |
| FID_INPUT_DATE_1 | 시작 날짜 | string | Y | 10 | YYYYMMDD |
| FID_INPUT_DATE_2 | 종료 날짜 | string | Y | 10 | YYYYMMDD |
| FID_PERIOD_DIV_CODE | 기간 분류 코드 | string | Y | 32 | `D`: 일, `W`: 주, `M`: 월, `Y`: 년 |

### Request Example (Python)

```python
import requests

url = "https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/inquire-daily-chartprice"

headers = {
    "content-type": "application/json",
    "authorization": f"Bearer {access_token}",
    "appkey": appkey,
    "appsecret": appsecret,
    "tr_id": "FHKST03030100"
}

params = {
    "fid_cond_mrkt_div_code": "N",
    "fid_input_iscd": ".DJI",
    "fid_input_date_1": "20240101",
    "fid_input_date_2": "20240128",
    "fid_period_div_code": "D"
}

response = requests.get(url, headers=headers, params=params)
print(response.json())
```

## Response

### Response Body

#### output1 (기본 정보)

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| hts_kor_isnm | HTS 한글 종목명 | string | |
| stck_shrn_iscd | 단축 종목코드 | string | |
| ovrs_nmix_prpr | 현재가 | string | |
| ovrs_nmix_prdy_vrss | 전일 대비 | string | |
| prdy_vrss_sign | 전일 대비 부호 | string | |
| prdy_ctrt | 전일 대비율 | string | |
| ovrs_nmix_prdy_clpr | 전일 종가 | string | |
| acml_vol | 누적 거래량 | string | |
| prdy_vol | 전일 거래량 | string | |
| ovrs_prod_oprc | 시가 | string | |
| ovrs_prod_hgpr | 최고가 | string | |
| ovrs_prod_lwpr | 최저가 | string | |

#### output2 (일자별 정보 - Array)

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| stck_bsop_date | 영업 일자 | string | YYYYMMDD |
| ovrs_nmix_prpr | 현재가(종가) | string | |
| ovrs_nmix_oprc | 시가 | string | |
| ovrs_nmix_hgpr | 최고가 | string | |
| ovrs_nmix_lwpr | 최저가 | string | |
| acml_vol | 누적 거래량 | string | |
| mod_yn | 변경 여부 | string | |

## 응답 코드 참고

### 대비 부호 (prdy_vrss_sign)

- `1`: 상한
- `2`: 상승
- `3`: 보합
- `4`: 하한
- `5`: 하락

### Response Example

```json
{
    "output1": {
        "acml_vol": "397268510",
        "hts_kor_isnm": "다우존스 산업지수",
        "ovrs_nmix_prdy_clpr": "31029.31",
        "ovrs_nmix_prdy_vrss": "-253.88",
        "ovrs_nmix_prpr": "30775.43",
        "ovrs_prod_hgpr": "30979.85",
        "ovrs_prod_lwpr": "30431.87",
        "ovrs_prod_oprc": "30790.00",
        "prdy_ctrt": "-0.82",
        "prdy_vrss_sign": "5",
        "stck_shrn_iscd": ".DJI"
    },
    "output2": [
        {
            "stck_bsop_date": "20220613",
            "ovrs_nmix_prpr": "30516.74",
            "ovrs_nmix_oprc": "31144.91",
            "ovrs_nmix_hgpr": "31144.91",
            "ovrs_nmix_lwpr": "30373.72",
            "acml_vol": "480501460",
            "mod_yn": "N"
        }
    ],
    "rt_cd": "0",
    "msg_cd": "MCA00000",
    "msg1": "정상처리 되었습니다."
}
```

## 활용 팁

1. **지수 및 환율 데이터**: 지수(`.DJI`, `.NAS` 등) 및 환율(`FX@KRW` 등) 데이터를 기간별로 가져와 차트 분석이나 통계 자료로 활용하기 적합합니다.
2. **미국 주요 종목 한정**: 본 API는 미국 주식의 경우 다우30, 나스닥100, S&P500 종목만 지원하므로, 일반 중소형주 시세는 전용 기간별 시세 API를 사용해야 합니다.
3. **부호 코드**: `prdy_vrss_sign` 값(1: 상한, 2: 상승, 3: 보합, 4: 하한, 5: 하락)을 통해 가격 등락 상태를 쉽게 파악할 수 있습니다.

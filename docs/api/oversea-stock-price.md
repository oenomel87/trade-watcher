# 한국투자증권 Open API - 해외주식 현재가 상세 가이드

## 기본 정보

| 항목 | 내용 |
|------|------|
| API 통신방식 | REST |
| 메뉴 위치 | [해외주식] 기본시세 |
| API 명 | 해외주식 현재가상세 |
| API ID | v1_해외주식-029 |
| 실전 TR_ID | HHDFS76200200 |
| 모의 TR_ID | 모의투자 미지원 |
| HTTP Method | GET |

## 엔드포인트

### 실전 환경
- **Domain**: `https://openapi.koreainvestment.com:9443`
- **URL**: `/uapi/overseas-price/v1/quotations/price-detail`

### 모의 환경
- **주의**: 해당 API는 모의투자 환경을 지원하지 않습니다.

## 개요

해외주식 현재가상세 API입니다.
해당 API를 활용하여 해외주식 종목의 매매단위(vnit), 호가단위(e_hogau), PER, PBR, EPS, BPS 등의 데이터를 확인하실 수 있습니다.

### 시세 지연 안내
- **무료 시세(지연 시세)**만 제공되며, API로는 유료 실시간 시세를 기본적으로 받아보실 수 없습니다.
- **미국**: 실시간 무료(0분 지연) - 단, 장중 시가는 상이할 수 있으며 익일 정정됨.
- **홍콩, 베트남, 중국, 일본**: 15분 지연
- **유료 실시간 시세**: HTS/MTS에서 유료 서비스 신청 후 접근토큰을 발급하면 실시간 시세 수신이 가능합니다. (신청 후 최대 2시간 소요)

## Request

### Request Header

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| content-type | 컨텐츠타입 | string | Y | 40 | `application/json; charset=utf-8` |
| authorization | 접근토큰 | string | Y | 350 | Bearer {access_token} |
| appkey | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey |
| appsecret | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret |
| personalseckey | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| tr_id | 거래ID | string | Y | 13 | `HHDFS76200200` |
| tr_cont | 연속 거래 여부 | string | N | 1 | |
| custtype | 고객 타입 | string | N | 1 | `B`: 법인, `P`: 개인 |
| seq_no | 일련번호 | string | N | 2 | [법인 필수] `001` |
| mac_address | 맥주소 | string | N | 12 | Mac address 값 |
| phone_number | 핸드폰번호 | string | N | 12 | [법인 필수] 하이픈 제거 |
| ip_addr | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자 IP Address |
| gt_uid | Global UID | string | N | 32 | [법인 전용] 거래고유번호 |

### Request Query Parameters

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| AUTH | 사용자권한정보 | string | Y | 32 | 공란 설정 가능 |
| EXCD | 거래소명 | string | Y | 4 | `HKS`: 홍콩<br/>`NYS`: 뉴욕<br/>`NAS`: 나스닥<br/>`AMS`: 아멕스<br/>`TSE`: 도쿄<br/>`SHS`: 상해<br/>`SZS`: 심천<br/>`SHI`: 상해지수<br/>`SZI`: 심천지수<br/>`HSX`: 호치민<br/>`HNX`: 하노이<br/>`BAY`: 뉴욕(주간)<br/>`BAQ`: 나스닥(주간)<br/>`BAA`: 아멕스(주간) |
| SYMB | 종목코드 | string | Y | 16 | 종목코드 (예: TSLA, AAPL) |

### Request Example (Python)

```python
import requests

# 접근 토큰은 미리 발급받았다고 가정
access_token = "your_access_token"
appkey = "your_appkey"
appsecret = "your_appsecret"

url = "https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/price-detail"

headers = {
    "content-type": "application/json; charset=utf-8",
    "authorization": f"Bearer {access_token}",
    "appkey": appkey,
    "appsecret": appsecret,
    "tr_id": "HHDFS76200200",
    "custtype": "P"
}

params = {
    "AUTH": "",
    "EXCD": "NAS",  # 나스닥
    "SYMB": "TSLA"  # 테슬라
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
| tr_cont | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 |
| gt_uid | Global UID | string | N | 32 | [법인 전용] 거래고유번호 |

### Response Body

#### 공통 응답 필드

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| rt_cd | 성공 실패 여부 | string | Y | 1 | 0: 성공, 그 외: 실패 |
| msg_cd | 응답코드 | string | Y | 8 | 응답 메시지 코드 |
| msg1 | 응답메세지 | string | Y | 80 | 응답 메시지 |

#### output (종목 상세 정보)

| Element | 한글명 | Type | Description |
|---------|--------|------|-------------|
| rsym | 실시간조회종목코드 | string | |
| pvol | 전일거래량 | string | |
| open | 시가 | string | |
| high | 고가 | string | |
| low | 저가 | string | |
| last | 현재가 | string | |
| base | 전일종가 | string | |
| tomv | 시가총액 | string | |
| pamt | 전일거래대금 | string | |
| uplp | 상한가 | string | |
| dnlp | 하한가 | string | |
| h52p | 52주최고가 | string | |
| h52d | 52주최고일자 | string | |
| l52p | 52주최저가 | string | |
| l52d | 52주최저일자 | string | |
| perx | PER | string | |
| pbrx | PBR | string | |
| epsx | EPS | string | |
| bpsx | BPS | string | |
| shar | 상장주수 | string | |
| mcap | 자본금 | string | |
| curr | 통화 | string | |
| zdiv | 소수점자리수 | string | |
| vnit | 매매단위 | string | |
| t_xprc | 원환산당일가격 | string | |
| t_xdif | 원환산당일대비 | string | |
| t_xrat | 원환산당일등락 | string | |
| p_xprc | 원환산전일가격 | string | |
| p_xdif | 원환산전일대비 | string | |
| p_xrat | 원환산전일등락 | string | |
| t_rate | 당일환율 | string | |
| p_rate | 전일환율 | string | |
| t_xsgn | 원환산당일기호 | string | HTS 색상표시용 |
| p_xsng | 원환산전일기호 | string | HTS 색상표시용 |
| e_ordyn | 거래가능여부 | string | (예: 매매 가능) |
| e_hogau | 호가단위 | string | |
| e_icod | 업종(섹터) | string | |
| e_parp | 액면가 | string | |
| tvol | 거래량 | string | |
| tamt | 거래대금 | string | |
| etyp_nm | ETP 분류명 | string | |

## 응답 코드 참고

### 원환산 기호 (t_xsgn, p_xsng)

- `1`: 상한
- `2`: 상승
- `3`: 보합
- `4`: 하한
- `5`: 하락

### Response Example

```json
{
    "output": {
        "rsym": "DNASTSLA",
        "zdiv": "4",
        "curr": "USD",
        "vnit": "1",
        "open": "257.2600",
        "high": "259.0794",
        "low": "242.0100",
        "last": "245.0100",
        "base": "258.0800",
        "pvol": "108861698",
        "pamt": "28090405673",
        "uplp": "0.0000",
        "dnlp": "0.0000",
        "h52p": "313.8000",
        "h52d": "20220921",
        "l52p": "101.8100",
        "l52d": "20230106",
        "perx": "69.51",
        "pbrx": "15.21",
        "epsx": "3.52",
        "bpsx": "16.11",
        "shar": "3173990000",
        "mcap": "3000000",
        "tomv": "777659289900",
        "t_xprc": "323658",
        "t_xdif": "17265",
        "t_xrat": "-5.06",
        "p_xprc": "0",
        "p_xdif": "0",
        "p_xrat": " 0.00",
        "t_rate": "1321.00",
        "p_rate": "",
        "t_xsgn": "5",
        "p_xsng": "3",
        "e_ordyn": "매매 가능",
        "e_hogau": "0.0100",
        "e_icod": "자동차",
        "e_parp": "0.0000",
        "tvol": "132541640",
        "tamt": "32907071789",
        "etyp_nm": ""
    },
    "rt_cd": "0",
    "msg_cd": "MCA00000",
    "msg1": "정상처리 되었습니다."
}
```

## 활용 팁

1. **환산 가격**: `t_xprc`, `t_xdif`, `t_xrat` 등을 통해 원화로 환산된 현재가 정보를 즉시 확인할 수 있습니다.
2. **거래소 구분**: 미국 주식의 경우 `NAS`(나스닥), `NYS`(뉴욕), `AMS`(아멕스) 구분을 정확히 입력해야 합니다. 주간 거래는 `BAQ`, `BAY`, `BAA` 코드를 사용합니다.
3. **재무 지표**: `perx`, `pbrx`, `epsx`, `bpsx` 등을 통해 해외 종목의 투자 지표를 분석할 수 있습니다.
4. **호가 및 매매 단위**: `vnit`(매매단위)와 `e_hogau`(호가단위)를 활용하여 정밀한 주문 시스템을 구축할 수 있습니다.

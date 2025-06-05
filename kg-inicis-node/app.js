// 환경변수 로드
require('dotenv').config();

const express = require("express"); 
const app = express();
const crypto = require('crypto'); 
const bodyParser = require("body-parser");
const request = require('request');

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended : true}));

app.set("views" , __dirname+"/views");
app.set("views engline" , "ejs");
app.engine("html", require("ejs").renderFile);

app.use(express.static("views"));  
const getUrl = require('./properties');

// 로깅 미들웨어 추가
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
    if (req.body && Object.keys(req.body).length > 0) {
        console.log('Request Body:', req.body);
    }
    next();
});

app.get("/" , (req,res) =>{
    const mid = process.env.MERCHANT_ID || "INIpayTest";                   // 상점아이디
    const signKey = process.env.SIGN_KEY || "SU5JTElURV9UUklQTEVERVNfS0VZU1RS"; // 환경변수에서 SignKey 로드
    const mKey = crypto.createHash("sha256").update(signKey).digest('hex'); // SHA256 Hash값 [대상: mid와 매칭되는 signkey]
    const oid = "INIpayTest_01234";                                         // 주문번호
    const price = "1000";                                                   // 결제금액
    const timestamp = new Date().getTime();                                 // 타임스템프 [TimeInMillis(Long형)]
    const use_chkfake = "Y";                             
    const signature  = crypto.createHash("sha256").update("oid="+oid+"&price="+price+"&timestamp="+timestamp).digest('hex'); //SHA256 Hash값 [대상: oid, price, timestamp]
    const verification = crypto.createHash("sha256").update("oid="+oid+"&price="+price+"&signKey="+signKey+"&timestamp="+timestamp).digest('hex'); //SHA256 Hash값 [대상: oid, price, signkey, timestamp]

    res.render("INIstdpay_pc_req.html" , {
        mid : mid,
        oid : oid,
        price : price,
        timestamp : timestamp,
        mKey : mKey,
        use_chkfake : use_chkfake,
        signature : signature,
        verification : verification
    });
});

app.post("/INIstdpay_pc_return.ejs" , (req , res) => {
    console.log("=== 결제 완료 콜백 수신 ===");
    console.log("Request Body:", req.body);
    
    try {
        if(req.body.resultCode === "0000"){
            console.log("결제 성공 - 승인 요청 진행");

            //############################################
            //1.전문 필드 값 설정(***가맹점 개발수정***)
            //############################################

            const mid = req.body.mid;                       // 상점아이디
            const signKey = process.env.SIGN_KEY || "SU5JTElURV9UUklQTEVERVNfS0VZU1RS"; // 환경변수에서 SignKey 로드
            const authToken = req.body.authToken;           // 승인요청 검증 토큰
            const netCancelUrl = req.body.netCancelUrl;     // 망취소요청 Url 
            const merchantData = req.body.merchantData;
            const timestamp = new Date().getTime();         // 타임스템프 [TimeInMillis(Long형)]
            const charset = "UTF-8";                        // 리턴형식[UTF-8,EUC-KR](가맹점 수정후 고정)
            const format = "JSON";                          // 리턴형식[XML,JSON,NVP](가맹점 수정후 고정)

            //##########################################################################
            // 승인요청 API url (authUrl) 리스트 는 properties 에 세팅하여 사용합니다.
            // idc_name 으로 수신 받은 센터 네임을 properties 에서 include 하여 승인 요청하시면 됩니다.
            //##########################################################################   

            const idc_name = req.body.idc_name;             
            const authUrl = req.body.authUrl;               // 승인요청 Url
            const authUrl2 = getUrl.getAuthUrl(idc_name);

            console.log(`IDC Name: ${idc_name}`);
            console.log(`Auth URL from request: ${authUrl}`);
            console.log(`Auth URL from properties: ${authUrl2}`);

            // SHA256 Hash값 [대상: authToken, timestamp]
            const signature  = crypto.createHash("sha256").update("authToken="+authToken+"&timestamp="+timestamp).digest('hex');

            // SHA256 Hash값 [대상: authToken, signKey, timestamp]
            const verification  = crypto.createHash("sha256").update("authToken="+authToken+"&signKey="+signKey+"&timestamp="+timestamp).digest('hex');
        
            
            //결제 승인 요청 
            let options = { 
                    mid : mid,
                    authToken : authToken, 
                    timestamp : timestamp,
                    signature : signature,
                    verification : verification,
                    charset : charset,
                    format : format
            };

            console.log("승인 요청 옵션:", options);

            if(authUrl == authUrl2) {
                console.log("URL 매칭 성공 - 승인 API 호출");

                request.post({method: 'POST', uri: authUrl2, form: options, json: true}, (err,httpResponse,body) =>{ 
                    
                    console.log("승인 API 응답 수신");
                    if (err) {
                        console.error("승인 API 오류:", err);
                    }
                    console.log("응답 상태:", httpResponse ? httpResponse.statusCode : 'No response');
                    console.log("응답 본문:", body);
                    
                    try{
                        let jsoncode = (err) ? err : JSON.stringify(body);
                        let result = JSON.parse(jsoncode);
                        
                        console.log("파싱된 결과:", result);
                        
                        res.render('INIstdpay_pc_return.ejs',{
                            resultCode : result.resultCode || '9999',
                            resultMsg : result.resultMsg || '응답 파싱 오류',
                            tid : result.tid || 'N/A',
                            MOID : result.MOID || req.body.oid,
                            TotPrice : result.TotPrice || req.body.price,
                            goodName : result.goodName || 'N/A',
                            applDate : result.applDate || 'N/A',
                            applTime : result.applTime || 'N/A'
                        });
                    }catch(e){
                        console.error("승인 응답 처리 오류:", e);
                        
                        // 망취소 처리
                        const netCancelUrl2 = getUrl.getNetCancel(idc_name);
                        console.log(`망취소 URL: ${netCancelUrl2}`);
                        
                        if(netCancelUrl == netCancelUrl2) {
                            request.post({method: 'POST', uri: netCancelUrl2, form: options, json: true}, (err,httpResponse,body) =>{
                                let result = (err) ? err : JSON.stringify(body);
                                console.log("망취소 결과:", result);
                            });
                        }
                        
                        // 오류 페이지 렌더링
                        res.render('INIstdpay_pc_return.ejs',{
                            resultCode : '9999',
                            resultMsg : '승인 처리 중 오류 발생',
                            tid : 'N/A',
                            MOID : req.body.oid || 'N/A',
                            TotPrice : req.body.price || 'N/A',
                            goodName : 'N/A',
                            applDate : 'N/A',
                            applTime : 'N/A'
                        });
                    }
                 });
            } else {
                console.error("URL 매칭 실패");
                res.render('INIstdpay_pc_return.ejs',{
                    resultCode : '9999',
                    resultMsg : 'URL 매칭 실패',
                    tid : 'N/A',
                    MOID : req.body.oid || 'N/A',
                    TotPrice : req.body.price || 'N/A',
                    goodName : 'N/A',
                    applDate : 'N/A',
                    applTime : 'N/A'
                });
            }
            
        } else {
            console.log("결제 실패 - 결과 코드:", req.body.resultCode);
            res.render('INIstdpay_pc_return.ejs',{
                resultCode : req.body.resultCode,
                resultMsg : req.body.resultMsg,
                tid : req.body.tid,
                MOID : req.body.MOID,
                TotPrice: req.body.TotPrice,
                goodName : req.body.goodName,
                applDate : req.body.applDate,
                applTime : req.body.applTime
            });
        }
    } catch (error) {
        console.error("전체 처리 오류:", error);
        res.status(500).render('INIstdpay_pc_return.ejs',{
            resultCode : '9999',
            resultMsg : '서버 처리 오류',
            tid : 'N/A',
            MOID : 'N/A',
            TotPrice : 'N/A',
            goodName : 'N/A',
            applDate : 'N/A',
            applTime : 'N/A'
        });
    }
});

app.get('/close', (req, res) => {
    res.send('<script language="javascript" type="text/javascript" src="https://stdpay.inicis.com/stdjs/INIStdPay_close.js" charset="UTF-8"></script>');
});

const PORT = process.env.PORT || 3000;

app.listen(PORT , (err) =>{
    if(err) return console.log(err);
    console.log(`The server is listening on port ${PORT}`);
});

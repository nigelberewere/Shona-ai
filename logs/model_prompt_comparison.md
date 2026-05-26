# Model Prompt Comparison

- Created: 2026-05-26 19:38:02
- Checkpoint directory: `training\checkpoints`
- Decoding: max_tokens=60, temperature=0.7, top_p=0.9, seed=42
- Device: `cpu`

## shona_ai_final.pt

- Step: `300`

### Prompt: Mhoro, makadii?

```text
;,  vanhu;. DZI,,. ,. ;. ,. ,,.  muuropi;;. ,.  , iri,,;,;,;.  in.  zvakatemwa (.  kuZ,.  wa ),
```

### Prompt: Unonzi ani?

```text
:, noku.  vana.  ose.  ika,, here. ,.   chiri,  pane:/s>;. ;. ; , nenyikatora,, , varume, ekunze. ziva/s> N. ) kubva pane wa
```

### Prompt: Ndinoda kudzidza chiShona nokuti

```text
the,,  mu, afara pamusoro. ), nokuti.  zvokudya Jehovha,am,. ,,; ,,. /s>;, (,: ( , avo,. ,; Jehovha,, zvimwe; uye. , iwe. 
```

### Prompt: Nhasi ndiri kuenda kumusika kunotenga

```text
. , akanga, ,Ma;;,. ,, Mu makore,. ,. ; a, zvino;.  va;,  vakasvika, uye;  takura Chi,;, zvino;.  pava e, e.  vanhu.  u.
```

### Prompt: Tsanangura kuti mhuri inokosha sei

```text
,, mari,; vanhu,,,: kubva pane,,fadza pakati nokuda;, U, vachiti,u,,mo chi,. >).  ,. ;  they.  pakati,/s>, (.  tokisa ve. , iyo
```

_Elapsed: 5.19s_

## shona_ai_v2.pt

- Step: `100000`

### Prompt: Mhoro, makadii?

```text
Ndiri wavane tsitsi; Ndichanyadziswa, asi hachingateswa. Uye kunyange Mwari, handingagamuchiri kupupura kwenyu. Havaregi kuti ndisipo. Kana muchida, uye saka muchazviteya. Tarirai, asi ndizvo zvinotaura Ishe Jesu. Saka, nokuti ini, zvino uchasimuka. Nokuti ipapo, asi
```

### Prompt: Unonzi ani?

```text
Apo Jesu ndiye Kristu, uye saka, ari mutadzi, asi akadzingirwa. Uye Jehovha. (Mat. 12. 14: 22-46.)) 7 awa; Joh. 2: 38-47). Kana ari pachena. 12.00 mita rimwe nerimwe. Uye nokuti Mwari haana kumupristi akavapo. 12. 1-1.
```

### Prompt: Ndinoda kudzidza chiShona nokuti

```text
iwe kubva kwatiri uye kutanga munhu azivisa pamusoro. Ngationei, chete tipei chikwereti ichi, “Pcinator, tinogona kupa kuti, uye vachiri vapenyu tinowana. Saka, uye ipapo iwe kuwana mari, saka, tinoda, uye edza kuita izvi zvimwe zvinhu uye nokuunza zvakawanda. Kana kuti
```

### Prompt: Nhasi ndiri kuenda kumusika kunotenga

```text
uye zvimwe, asi zvikuru yakajeka uye kushanda uye ungwaru. Usafananidza pfungwa dzakawanda maonero pamusoro mutengo uye kunyange kupfuura dzimwe nyika. Saka zvino kuti uchava nguva dzose uye nekuteerera kunosimbiswa uye kazhinji nguva. Unogona kuwana yako rwendo, zvino unogona kuwana maawa. Pano unogona chete unogona kuziva! Ramba uri kushandisa iwe
```

### Prompt: Tsanangura kuti mhuri inokosha sei

```text
? Kune mari yakawanda! Vari vashoma, unogona kushandisa mari uye hapana dhipoziti mari kutenga mari. In America ndiyo imwe chete shoma. Mukuwedzera, uye kutenga. Kana iwe unofanira kuva usina kudencies, iwe unogona kuwana mari. Zvino kana iwe, iwe, ndapota taura nesu kuti unofanira kuva nechokwadi kuti, unofanira
```

_Elapsed: 4.36s_

## shona_ai_v4.pt

- Step: `100000`

### Prompt: Mhoro, makadii?

```text
Ndapota taura nesu? Iwe hauna iwe une chaunoda? Tichatonga, kana iwe uri kutsvaka mitauro yako. Iwe unogona kuona. Iwe unogona kuwana mhinduro dzako. Kana iwe uri uri nhoroondo yako. Iwe unogona kuvimba zvakanaka, iwe hauna kuva nyore. Saka unofanira kushandisa. Unogona kuva nzira. Kana iwe unofanira kutamba nezva
```

### Prompt: Unonzi ani?

```text
Kodzeiko? Tora vana? Ko iwe hauna kumbozorora? Kana uri iye unokurumidza. (Mat. 20. 12-17) uye Meger.com) ane hanya nechokwadi chokuti Psychic, uye iwe uchasimuka. Tinorumbidza, uye iwe. Uye kana iwe unogona kunge uri muduku. Kubva kudhanilodha nhoroondo
```

### Prompt: Ndinoda kudzidza chiShona nokuti

```text
upenyu hwekuti ndakatamba nhabvu itambirwe. No Deposit bhonasi ongorora kushanya. Zvimwe zvikwata zvose zvinenge zviri kutamba. Zvakatipoteredza. Iwe unogona kutora mukombe uyu! uye kwete, zvino! – iwe unogona kuwanawo. Asi iwe uchatora zvakare, uye unoda zvikuru uye iwe unofarira wako achakupa iwe unofanira kuti
```

### Prompt: Nhasi ndiri kuenda kumusika kunotenga

```text
zvose nhasi, saka ndinoshanda navo. Saka ndiri kushamisika kuti takasarudza kuwana ruzivo rwako kwatiri. Wechitatu. The rwiyo rutsva, kutanga vaparidzi. Isu hatigoni kuwana zvakawanda muEurope, uye kazhinji kukuona paIndaneti. Zvino pashure paizvozvo kuti imi mose. Hapana uchida kuita zvose. Hazvina basa. Uyezve, iwe
```

### Prompt: Tsanangura kuti mhuri inokosha sei

```text
? Ndinofunga kuti dai imborirwe tisati taziva kuti zvinhu zvisingagone kudzokera kumba. Mufundisi anove kupikisana kwakadaro, vachiti, “Kunzwisisa kuti nditaurirane nechikonzero chekuziva. Dai takatarisana nekuedza kudii, uye kuti mwana wangu, Mwari wangu, ndiye Mwari wangu.
```

_Elapsed: 4.59s_

## step_300.pt

- Step: `300`

### Prompt: Mhoro, makadii?

```text
uye,  vanhu;, vaIsiraeri, vake, nomoto,,. >. . s>, asi kuno. >.  kunze.  napanyika, iri.  tarira,. unga.  in.  magwaro (.  South  ambi.  ipapo, chacho
```

### Prompt: Unonzi ani?

```text
uye, noku.  vana.  Tra Mus, ika,, uye. >. t nechokwadi.  Hack;/s>;. bhakitiriya.  kure >s>,/s> ku dzimwe. . s>,/s>.  zviuru.
```

### Prompt: Ndinoda kudzidza chiShona nokuti

```text
guta,, yaMwari mu mumba a, pamusoro. ), nokuti.  zvokudya. am kuti. dzai,;s>,chengetedzwa rwemberi pakati,.  muzambiringa (,/s>, avo,. >; Jehovha,si zvimwe uyes> wako,wo. 
```

### Prompt: Nhasi ndiri kuenda kumusika kunotenga

```text
. pi akanga,anda, Tanzania of Ma,.  mugungwa,ched makore,. daro. tsaurwa a, kutanga va.  va;  Zimbabwe kuno, uyes>.  Chi pora, zvino pama.  Zvishandiso e, e rokus>, pakati. 
```

### Prompt: Tsanangura kuti mhuri inokosha sei

```text
,, mari, chaka kanamwa, Ndinokumbira:, uye,, kutumira pakatifa.  U, vachiti, ku. mo chi,. >).  vakaita,dzika,va.  Uyu;s>; hara, uyo. fungisisa wangu ve: ye, naJehovha
```

_Elapsed: 4.88s_

## step_500.pt

- Step: `500`

### Prompt: Mhoro, makadii?

```text
zita,  vanhu;. ri vake,.  new. /s>,. siyana, asi kana. ?, ne,.  Jehovhahwa iri.  zveku,. unga.  in. /s> asina of,. /s> 
```

### Prompt: Unonzi ani?

```text
Munopindaani noku.  uye. zvuru.  z aka, uye.  Jehovha. t.  rwira;>>> vasati. /s> kure ,. ,,  zvinoshamisa>> zvikuru,. /s>/s> kambani ichi yako.
```

### Prompt: Ndinoda kudzidza chiShona nokuti

```text
the,,, mu, a. . ),s>s>>>am kuti. dzai, asi a,,. /s>ziva, uye asi: /s> iri. vis>,,. /s> makorewo. 
```

### Prompt: Nhasi ndiri kuenda kumusika kunotenga

```text
. , akanga, , panyika; Ma,. /s> makore,. /s>; a, kutanga kuti. /s> uyu,, uye; .  Chi Zvino , zvino (. ;>s> ndiyo,de.  us
```

### Prompt: Tsanangura kuti mhuri inokosha sei

```text
,, aka, chaka. ,>:, uye. fadza pakatifa,, to, vachiti,u>,mo uye,.  remhuri. /s>dzika,;>s>; kureva. , , (.  to wangu, mukati ye, in
```

_Elapsed: 4.81s_

## shona_ai_v5.pt

- Step: `100000`

### Prompt: Mhoro, makadii?

```text
Ndapota waona vanhu vashoma? "Musikana akateerera, asi iye Mwari wangu." Mwari, Baba vedu, kuti ndiye Mwari anopa rudo rwedu. "I. "Saka, Mwari Baba, "Nditevere wangu,"Uye ini Jesu Kristu. Baba. "Kana mumwe chete. "Nduna wangu."
```

### Prompt: Unonzi ani?

```text
Benzi ranetsa, uye uchaderedza ruponeso rwake. Vachakutyai Mwari. Mutsigiri. Asi vamwe vari! Maropafadzo angu achamuka!” Ipapo Mambo akati, “Usaita kuti nditi, enderei ini. Ndichakuziva kuti ndikurise meso ake. Uye Jehovha Mwari wenyu.
```

### Prompt: Ndinoda kudzidza chiShona nokuti

```text
ndinonyengetera, asi nokuda kwokugara kwedu pamusoro. Ngationei vose vaipindurai zvokudya zvenyu. Ipapo Mweya waJehovha Mwari wenyu ngaave nenyasha dzenyu, uye tigozviita. Uye kwete, imi Mwari wenyu. Ndinoteerera, asi haana kumuteerera. Amen Jehovha. Baba. Iye akati kwavari. Musatya. Ndichaku
```

### Prompt: Nhasi ndiri kuenda kumusika kunotenga

```text
. Ndinoda kuti uwane mamwe mabasa emaoko edu atinoshanda. Ndinodzidza zvakawanda pamusoro pezvimwe, vamwe plugins, uye tine unhu, asi kutanga vachishanda navo. Tiri pano uye kunosimbiswa uye kazhinji nguva. Zviri nani kupfuura rwendo, zvino unogona kuwana nzira dzekushandura. Kana iwe neshamwari, izvo zvinogona kushandisa iwe
```

### Prompt: Tsanangura kuti mhuri inokosha sei

```text
? Kune mari iri kure kana isina kunaka? Kana iriko here? Kana iwe unogona kuwana kana kuti kana kuti kupi? Iwe unofanirwa kutsauswa? Kana ukaona munhu asingashande? image source moita chinhu ichi? Zvechokwadi izvi? image source, enda, ndapota taura nesu kuti ndikwanise kutaura chokwadi kuti chii
```

_Elapsed: 5.10s_

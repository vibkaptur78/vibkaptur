<?php
/* ============================================================================
   VIBKAPTUR — Relay de avisos por correo (Brevo / transaccional)
   La API key vive AQUÍ, en el servidor. Nunca en el index.html.
   Colocar en el VPS como:  /var/www/vibkaptur/public/api/aviso.php
   y en index.html poner BREVO.ready = true  (endpoint '/api/aviso.php').
   ----------------------------------------------------------------------------
   PASO ÚNICO cuando tengas la key: sustituye BREVO_KEY por tu clave de Brevo
   (Brevo > SMTP & API > API Keys). El remitente debe ser un dominio verificado
   en Brevo (aquí: avisos@vibkaptur.com).
   ============================================================================ */

const BREVO_KEY = 'PON_AQUI_TU_API_KEY_DE_BREVO';           // <-- único dato a rellenar
const FROM_EMAIL = 'avisos@vibkaptur.com';
const FROM_NAME  = 'VIBKAPTUR · Ingenor';

header('Content-Type: application/json');

// Solo acepta POST del propio sitio
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo '{"error":"method"}'; exit; }

$in = json_decode(file_get_contents('php://input'), true);
if (!$in) { http_response_code(400); echo '{"error":"bad_json"}'; exit; }

$toEmail = isset($in['to']) ? $in['to'] : '';
$toName  = isset($in['toName']) ? $in['toName'] : 'Técnico';
$subject = isset($in['subject']) ? $in['subject'] : 'Revisión VIBKAPTUR';
$planta  = isset($in['planta']) ? $in['planta'] : '';
$tecnica = isset($in['tecnica']) ? $in['tecnica'] : '';
$periodo = isset($in['periodo']) ? $in['periodo'] : '';
$cc      = isset($in['cc']) && is_array($in['cc']) ? $in['cc'] : array();
$corr    = isset($in['corregido']) && is_array($in['corregido']) ? $in['corregido'] : array();
$rev     = isset($in['revisar']) && is_array($in['revisar']) ? $in['revisar'] : array();

function li($arr){ $h=''; foreach($arr as $x){ $t=htmlspecialchars($x['t']); $d=htmlspecialchars($x['d']); $h.="<li><b>$t:</b> $d</li>"; } return $h ?: '<li>—</li>'; }

$html = '<div style="font-family:Arial,sans-serif;max-width:560px">'
      . '<div style="background:#0d2d46;color:#fff;padding:12px 16px;font-weight:bold">Ingenor · VIBKAPTUR — Revisión de informe</div>'
      . '<div style="padding:16px 18px;color:#333">'
      . '<p>Hola '.htmlspecialchars($toName).',</p>'
      . '<p>He revisado el informe de <b>'.htmlspecialchars($planta).'</b> ('.htmlspecialchars($tecnica).', '.htmlspecialchars($periodo).').</p>'
      . '<p style="font-weight:bold;margin:12px 0 4px">Corregido automáticamente</p><ul>'.li($corr).'</ul>'
      . '<p style="font-weight:bold;margin:12px 0 4px">Para que revises</p><ul>'.li($rev).'</ul>'
      . '<p>Cuando lo revises, dame el OK y lo publico.</p>'
      . '<p>— VIBKAPTUR · revisión automática</p>'
      . '</div></div>';

$to = array();
if ($toEmail) $to[] = array('email'=>$toEmail, 'name'=>$toName);
$ccArr = array();
foreach ($cc as $e) { $ccArr[] = array('email'=>$e); }
if (!$to) $to = $ccArr;   // si no hay técnico, al menos a la copia

$body = array(
  'sender'  => array('email'=>FROM_EMAIL, 'name'=>FROM_NAME),
  'to'      => $to,
  'cc'      => $ccArr,
  'subject' => $subject,
  'htmlContent' => $html
);

$ch = curl_init('https://api.brevo.com/v3/smtp/email');
curl_setopt_array($ch, array(
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_POST => true,
  CURLOPT_HTTPHEADER => array('accept: application/json','api-key: '.BREVO_KEY,'content-type: application/json'),
  CURLOPT_POSTFIELDS => json_encode($body)
));
$resp = curl_exec($ch);
$code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($code >= 200 && $code < 300) { echo json_encode(array('ok'=>true)); }
else { http_response_code(502); echo json_encode(array('error'=>'brevo','code'=>$code,'detail'=>$resp)); }

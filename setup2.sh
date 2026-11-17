#!/bin/sh
# ============================================================================
# VIBKAPTUR — instalador del relay de avisos por correo (Brevo, server-side)
# Uso:  curl -sL <raw setup2.sh> | sh -s 'TU_API_KEY_BREVO'
# La clave queda SOLO en el servidor (no en el repositorio).
# ============================================================================
KEY="$1"
if [ -z "$KEY" ]; then echo "Falta la API key: ... | sh -s 'xkeysib-...'"; exit 1; fi
D=/var/www/vibkaptur/public/api
mkdir -p "$D"
cat > "$D/aviso.php" <<'PHP'
<?php
header('Content-Type: application/json');
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo '{"error":"method"}'; exit; }
$KEY = '__KEY__';
$FROM = array('email' => 'pedro.ortega@ingenorsistemas.com', 'name' => 'VIBKAPTUR - Ingenor');
$TECNICOS = array(
  array('email'=>'tecnico1@ingenorsistemas.com'),
  array('email'=>'tecnico2@ingenorsistemas.com'),
  array('email'=>'tecnico3@ingenorsistemas.com'),
  array('email'=>'tecnico4@ingenorsistemas.com'),
  array('email'=>'pedro.ortega@ingenorsistemas.com')
);
$CC = array(array('email'=>'administracion@ingenorsistemas.com'));
$in = json_decode(file_get_contents('php://input'), true);
if (!$in) { http_response_code(400); echo '{"error":"bad_json"}'; exit; }
$type    = isset($in['type']) ? $in['type'] : 'review';
$subject = isset($in['subject']) ? $in['subject'] : 'Aviso VIBKAPTUR';
$html    = isset($in['html']) ? $in['html'] : '<p>(sin contenido)</p>';

if ($type === 'client') {
  // Email al cliente: destinatario provisto por la app; administracion en copia.
  $to = array();
  if (!empty($in['to'])) { foreach ((array)$in['to'] as $e) { $to[] = array('email'=>$e); } }
  if (!$to) { http_response_code(400); echo '{"error":"no_recipient"}'; exit; }
  $cc = $CC;
} else {
  // Aviso de publicacion al equipo tecnico + Pedro; administracion en copia.
  $to = $TECNICOS;
  $cc = $CC;
}

$body = array('sender'=>$FROM, 'to'=>$to, 'cc'=>$cc, 'subject'=>$subject, 'htmlContent'=>$html);
$ch = curl_init('https://api.brevo.com/v3/smtp/email');
curl_setopt_array($ch, array(
  CURLOPT_RETURNTRANSFER=>true, CURLOPT_POST=>true,
  CURLOPT_HTTPHEADER=>array('accept: application/json','api-key: '.$KEY,'content-type: application/json'),
  CURLOPT_POSTFIELDS=>json_encode($body)
));
$resp = curl_exec($ch); $code = curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
if ($code >= 200 && $code < 300) { echo json_encode(array('ok'=>true)); }
else { http_response_code(502); echo json_encode(array('error'=>'brevo','code'=>$code,'detail'=>$resp)); }
PHP
# Inyecta la clave solo en el archivo del servidor
sed -i "s|__KEY__|$KEY|" "$D/aviso.php"
chmod 644 "$D/aviso.php"
echo "OK: aviso.php instalado en $D"

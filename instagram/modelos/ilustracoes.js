// Ilustrações em traço (viewBox 400x300) usadas nos posts e nos vídeos da série "sonho".
const ILUSTRACOES = {
  casa: `
    <path d="M40 152 L200 38 L360 152"/>
    <path d="M78 126 L78 268 L322 268 L322 126"/>
    <path d="M176 268 L176 196 L224 196 L224 268"/>
    <path d="M108 172 H152 V214 H108 Z"/>
    <path d="M248 172 H292 V214 H248 Z"/>
    <path d="M130 172 V214 M108 193 H152 M270 172 V214 M248 193 H292"/>
    <path d="M268 88 L268 56 L298 56 L298 109"/>
    <circle cx="214" cy="234" r="3.5"/>
    <path d="M18 268 H382"/>`,
  chave: `
    <path d="M52 158 L118 100 L184 158 L184 226 L52 226 Z"/>
    <circle cx="118" cy="176" r="20"/>
    <path d="M184 186 H368"/>
    <path d="M336 186 V220 H352 V186"/>
    <path d="M300 186 V210 H314 V186"/>
    <path d="M368 186 L368 172 L184 172"/>`,
  carro: `
    <path d="M40 206 L40 172 Q42 156 62 151 L112 140 L152 106 Q162 98 178 98 L264 98 Q280 98 292 108 L330 140 L354 146 Q370 150 370 168 L370 206"/>
    <path d="M40 206 H78 M142 206 H268 M332 206 H370"/>
    <circle cx="110" cy="206" r="31"/>
    <circle cx="300" cy="206" r="31"/>
    <circle cx="110" cy="206" r="9"/>
    <circle cx="300" cy="206" r="9"/>
    <path d="M164 140 L184 113 L244 113 L244 140 Z"/>
    <path d="M256 140 L256 113 L276 113 L302 140 Z"/>
    <path d="M250 148 V196 M350 160 H364"/>
    <path d="M18 240 H382"/>`,
  moto: `
    <circle cx="96" cy="206" r="48"/>
    <circle cx="306" cy="206" r="48"/>
    <circle cx="96" cy="206" r="34"/>
    <circle cx="306" cy="206" r="34"/>
    <circle cx="96" cy="206" r="7"/>
    <circle cx="306" cy="206" r="7"/>
    <path d="M176 160 H236 V200 H176 Z"/>
    <path d="M188 172 H224 M188 186 H224"/>
    <path d="M96 206 L162 150 L252 150 L306 206"/>
    <path d="M146 140 Q172 116 214 124 L262 127 Q278 130 282 144"/>
    <path d="M306 206 L272 108"/>
    <path d="M254 98 L288 108"/>
    <path d="M176 206 H244"/>
    <circle cx="290" cy="126" r="7"/>
    <path d="M18 256 H382"/>`,
};

function ilustracao(nome, classe = "ilu") {
  return `<svg class="${classe}" viewBox="0 0 400 300" fill="none" stroke-linecap="round" stroke-linejoin="round">${ILUSTRACOES[nome]}</svg>`;
}

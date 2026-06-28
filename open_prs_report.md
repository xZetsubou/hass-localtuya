# PRs abertos - xZetsubou/hass-localtuya

Gerado em: 2026-06-26 13:24:21 -03:00
Total de PRs abertos: 17

## PR #815: Add a feature to apply a constant offset to sensor values

- URL: https://github.com/xZetsubou/hass-localtuya/pull/815
- Autor: phoeagon (@phoeagon)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `master` -> `master`
- Criado em: 2026-06-15T07:28:40Z; Atualizado em: 2026-06-15T07:28:40Z
- Mudancas: +87/-5; arquivos alterados: 13

### Descricao

Atualmente, a configuração permite aplicar apenas um fator de escala.

Isso muitas vezes não é suficiente, porque o SmartLife frequentemente usa valores baseados em incrementos sobre uma base.

Na prática, precisamos de uma transformação linear do tipo `y = kx + b`; o fator de escala cobre `k`, e este PR adiciona o offset `b`.

O offset é aplicado depois do fator de escala para facilitar a depuração e o ajuste do valor.

Foi testado no Home Assistant e o funcionamento foi confirmado.

Obrigado!

### Commits

- `8a7cf57` add an offset, to be applied after scaling factor, for most sensors w…
- `527f15a` reformatting to make linter happy

### Arquivos modificados

- `custom_components/localtuya/const.py` (MODIFIED, +1/-0)
- `custom_components/localtuya/entity.py` (MODIFIED, +9/-3)
- `custom_components/localtuya/number.py` (MODIFIED, +10/-1)
- `custom_components/localtuya/sensor.py` (MODIFIED, +4/-1)
- `custom_components/localtuya/strings.json` (MODIFIED, +1/-0)
- `custom_components/localtuya/translations/en.json` (MODIFIED, +1/-0)
- `custom_components/localtuya/translations/it.json` (MODIFIED, +1/-0)
- `custom_components/localtuya/translations/pl.json` (MODIFIED, +1/-0)
- `custom_components/localtuya/translations/pt-BR.json` (MODIFIED, +1/-0)
- `custom_components/localtuya/translations/tr.json` (MODIFIED, +1/-0)
- `custom_components/localtuya/translations/vi.json` (MODIFIED, +1/-0)
- `custom_components/localtuya/translations/zh-Hans.json` (MODIFIED, +1/-0)
- `tests/test_number.py` (MODIFIED, +55/-0)

### Comentarios e reviews

- Comentarios: 0; Reviews: 0

## PR #809: fix: v3.5 session key negotiation failures on reconnect

- URL: https://github.com/xZetsubou/hass-localtuya/pull/809
- Autor: Kilian von Pflugk (@jumoog)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `xZetsubou_Fix` -> `master`
- Criado em: 2026-05-30T17:48:58Z; Atualizado em: 2026-05-30T19:52:11Z
- Mudancas: +7/-1; arquivos alterados: 2

### Descricao

- Corrige uma atribuição invertida em `clean_up_session()`: antes ela sobrescrevia `real_local_key` com a chave da sessão, fazendo a próxima reconexão criptografar `SESS_KEY_NEG_START` com uma chave de sessão antiga em vez da chave do dispositivo.
- Redefine `dispatcher.local_key` para `real_local_key` no início de `_negotiate_session_key()`, para que a resposta `SESS_KEY_NEG_RESP` seja descriptografada com a chave correta.
- Inicializa `rkey = None` antes do bloco `try`, evitando `NameError` caso uma exceção ocorra enquanto o dispositivo ainda está conectado.

### Commits

- `4e3a6db` fix: v3.5 session key negotiation failures on reconnect
- `95d2ffb` fix: auto protocol stops at v3.4 when device is v3.5

### Arquivos modificados

- `custom_components/localtuya/config_flow.py` (MODIFIED, +4/-0)
- `custom_components/localtuya/core/pytuya/__init__.py` (MODIFIED, +3/-1)

### Comentarios e reviews

- Comentarios: 0; Reviews: 0

## PR #807: Per device logging

- URL: https://github.com/xZetsubou/hass-localtuya/pull/807
- Autor: Olaf Marzocchi (@dewi-ny-je)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `per_device_logging` -> `master`
- Criado em: 2026-05-20T09:14:41Z; Atualizado em: 2026-05-20T13:42:06Z
- Mudancas: +19/-3; arquivos alterados: 4

### Descricao

Resolve #805.

### Commits

- `ccbe830` Add debug option for unreachable errors
- `231da0f` Improve error logging for connection failures
- `e3eba18` Add CONF_DEBUG_UNREACHABLE_ERRORS to config flow
- `c362971` Update en.json

### Arquivos modificados

- `custom_components/localtuya/config_flow.py` (MODIFIED, +7/-0)
- `custom_components/localtuya/const.py` (MODIFIED, +4/-0)
- `custom_components/localtuya/coordinator.py` (MODIFIED, +5/-1)
- `custom_components/localtuya/translations/en.json` (MODIFIED, +3/-2)

### Comentarios e reviews

- Comentarios: 1; Reviews: 0
  - Comentario de @dewi-ny-je em 2026-05-20T13:42:06Z: I am using it and it works, the failed checks seem to be related to billing issues I have no idea about

## PR #806: Change some entities from config to diagnostic

- URL: https://github.com/xZetsubou/hass-localtuya/pull/806
- Autor: Olaf Marzocchi (@dewi-ny-je)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `config_to_diagnostic` -> `master`
- Criado em: 2026-05-20T09:09:21Z; Atualizado em: 2026-05-20T13:42:09Z
- Mudancas: +43/-14; arquivos alterados: 2

### Descricao

Resolve #798.

### Commits

- `d81d35b` Refactor entity_category for better compatibility
- `8408726` Update entity category handling for sensor platforms
- `b5e7f77` Normalize entity category documentation for clarity

### Arquivos modificados

- `custom_components/localtuya/config_flow.py` (MODIFIED, +11/-1)
- `custom_components/localtuya/entity.py` (MODIFIED, +32/-13)

### Comentarios e reviews

- Comentarios: 1; Reviews: 0
  - Comentario de @dewi-ny-je em 2026-05-20T13:42:08Z: I am using it and it works, the failed checks seem to be related to billing issues I have no idea about

## PR #802: Change liquid depth sensor unit conversion factor

- URL: https://github.com/xZetsubou/hass-localtuya/pull/802
- Autor: Kaew (@iKaew)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `fix-liquid-depth-unit-scale-factor` -> `master`
- Criado em: 2026-05-05T08:15:22Z; Atualizado em: 2026-05-15T07:53:47Z
- Mudancas: +1/-1; arquivos alterados: 1

### Descricao

Corrige #801: aplica o fator de escala à unidade do sensor de profundidade de líquido para que ela corresponda ao valor reportado e ao valor máximo de profundidade exibido em metros.

### Commits

- `f86c034` Change liquid depth sensor unit conversion factor

### Arquivos modificados

- `custom_components/localtuya/core/ha_entities/sensors.py` (MODIFIED, +1/-1)

### Comentarios e reviews

- Comentarios: 1; Reviews: 0
  - Comentario de @iKaew em 2026-05-15T07:53:47Z: Hi @xZetsubou , Is there any chance you can review this ?

## PR #796: feat: expose update_dps as a Home Assistant service

- URL: https://github.com/xZetsubou/hass-localtuya/pull/796
- Autor: Facundo Paredes (@facuparedes)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `feature/expose-update-dps-service` -> `master`
- Criado em: 2026-04-20T16:59:39Z; Atualizado em: 2026-04-20T16:59:39Z
- Mudancas: +54/-0; arquivos alterados: 2

### Descricao

#### Resumo

- Adiciona um novo serviço `localtuya.update_dps`, que envia o comando de protocolo Tuya `UPDATEDPS` (`0x12`) para solicitar valores atualizados de datapoints de um dispositivo.
- Aceita um parâmetro opcional `dps` para especificar quais índices de DP devem ser atualizados. Se omitido, usa todos os DPs detectados e permitidos.
- Permite atualizar DPs sob demanda por automações e scripts, sem exigir um `scan_interval` constante.

#### Motivação

Atualmente, a única forma de acionar o comando `UPDATEDPS` é pelo temporizador periódico `scan_interval`. Isso significa que usuários que querem dados atualizados de monitoramento de energia, como corrente, potência e tensão, normalmente nos DPs 18, 19 e 20, precisam configurar um intervalo fixo de polling que roda continuamente, mesmo quando o dispositivo está ocioso.

Ao expor `update_dps` como serviço, os usuários podem criar automações mais inteligentes que consultam o dispositivo apenas quando necessário. Por exemplo: atualizar os DPs de energia a cada poucos segundos somente enquanto uma tomada inteligente está em uso, e parar quando ela estiver desligada.

#### Exemplo de automação
```yaml
automation:
  - alias: "Poll energy only when plug is on"
    trigger:
      - platform: time_pattern
        seconds: "/10"
    condition:
      - condition: state
        entity_id: switch.my_plug
        state: "on"
    action:
      - action: localtuya.update_dps
        data:
          device_id: "my_device_id"
          dps:
            - 18
            - 19
            - 20
```

#### Alterações

- `__init__.py`: adiciona o schema `SERVICE_UPDATE_DPS`, o handler `_handle_update_dps` e o registro do serviço.
- `services.yaml`: adiciona a definição do serviço `update_dps`, com os campos `device_id` e `dps` opcional.

#### Plano de testes

- [x] Testado manualmente em uma tomada inteligente Tuya; chamar o serviço atualiza `last_updated` nas entidades de sensor de energia.
- [ ] Verificar o comportamento com subdispositivos (`gateway` + `node_id`).
- [ ] Verificar o comportamento quando o parâmetro `dps` é omitido. Deve atualizar todos os DPs permitidos.
- [ ] Verificar o tratamento de erro quando o dispositivo está desconectado.

### Commits

- `56f2d70` feat: expose update_dps as a Home Assistant service

### Arquivos modificados

- `custom_components/localtuya/__init__.py` (MODIFIED, +35/-0)
- `custom_components/localtuya/services.yaml` (MODIFIED, +19/-0)

### Comentarios e reviews

- Comentarios: 0; Reviews: 0

## PR #794: [codex] add event-driven low-power device support

- URL: https://github.com/xZetsubou/hass-localtuya/pull/794
- Autor: need2rzn (@need2rzn)
- Estado: OPEN; Draft: sim; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `codex/low-power-event-driven` -> `master`
- Criado em: 2026-04-16T19:08:04Z; Atualizado em: 2026-04-19T19:45:51Z
- Mudancas: +126/-12; arquivos alterados: 7

### Descricao

#### Resumo
- Adiciona uma opção dedicada `device_event_driven` para dispositivos de baixo consumo que acordam apenas quando ocorre um evento.
- Pula loops de heartbeat e refresh para dispositivos orientados por evento, mantendo o último estado conhecido disponível.
- Documenta a nova opção e cobre o comportamento com testes focados.

#### Por quê
Alguns sensores Wi-Fi alimentados por bateria não reportam em um intervalo fixo. Eles acordam apenas quando um evento ocorre, como movimento ou mudança de aberto/fechado. Tratá-los como dispositivos que dormem por tempo fixo pode causar keep-alives desnecessários, tentativas de atualização e alternância indevida para estado indisponível.

#### Validação
- `uv run --python 3.12 --prerelease=allow --with-requirements requirements_test.txt pytest`

### Commits

- `c8cda06` add event-driven low-power device support

### Arquivos modificados

- `custom_components/localtuya/config_flow.py` (MODIFIED, +7/-1)
- `custom_components/localtuya/const.py` (MODIFIED, +4/-0)
- `custom_components/localtuya/coordinator.py` (MODIFIED, +10/-2)
- `custom_components/localtuya/translations/en.json` (MODIFIED, +8/-7)
- `documentation/docs/faq/index.md` (MODIFIED, +1/-1)
- `documentation/docs/usage/configure_add_device.md` (MODIFIED, +4/-1)
- `tests/test_low_power.py` (ADDED, +92/-0)

### Comentarios e reviews

- Comentarios: 0; Reviews: 0

## PR #792: fix(fan): respect fan_dps_type config for speed control

- URL: https://github.com/xZetsubou/hass-localtuya/pull/792
- Autor: Veszprémi Balázs (@veszpa)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `fix/fan-dps-type-str` -> `master`
- Criado em: 2026-04-10T09:35:33Z; Atualizado em: 2026-04-10T09:35:33Z
- Mudancas: +8/-5; arquivos alterados: 1

### Descricao

#### Resumo
- Alguns dispositivos Tuya usam **valores DPS do tipo string** para velocidade do ventilador, por exemplo `"5"` em vez de `5`.
- A opção de configuração `fan_dps_type` existe para isso, mas **não era usada** no caminho de código de valor por faixa em `async_set_percentage`.
- Isso causava erros `Command 7 timed out waiting for sequence number` ao definir a velocidade do ventilador, porque o dispositivo rejeitava silenciosamente valores inteiros.

#### Causa raiz
Em `fan.py`, o caminho de lista ordenada envia corretamente a velocidade como `str()`, mas o caminho de valor por faixa sempre enviava `int()`, ignorando `CONF_FAN_DPS_TYPE`.

#### Correção
Verifica `CONF_FAN_DPS_TYPE` e converte o valor de velocidade para `str` quando configurado como `"str"`.

#### Testes
- Inspeção manual do código.
- A correção é direcionada apenas à escrita de DPS de velocidade por faixa do ventilador.

### Commits

- `90502a0` fix(fan): respect fan_dps_type config for speed control

### Arquivos modificados

- `custom_components/localtuya/fan.py` (MODIFIED, +8/-5)

### Comentarios e reviews

- Comentarios: 0; Reviews: 0

## PR #790: fix(vacuum): fault_dp non-zero value incorrectly overrides vacuum status with ERROR

- URL: https://github.com/xZetsubou/hass-localtuya/pull/790
- Autor: t34wrj (@t34wrj)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `master` -> `master`
- Criado em: 2026-03-28T15:16:23Z; Atualizado em: 2026-03-31T09:02:54Z
- Mudancas: +0/-3; arquivos alterados: 2

### Descricao

Corrige #789.

#### Resumo

Remove a sobrescrita do estado `ERROR` em `vacuum.py`, que era acionada sempre que `fault_dp != 0`, e remove `fault_dp` da autoconfiguração da categoria `sd` em `vacuums.py`.

#### Problema

A verificação `!= 0` em `status_updated()` trata qualquer valor não zero no bitfield de falha como estado de erro, sobrescrevendo incondicionalmente o estado de atividade resolvido corretamente a partir do DPS de status. No Lubluelu SL60D, e potencialmente em outros aspiradores da categoria `sd`, o DPS de falha contém bits informativos que permanecem não zero durante a operação normal, fazendo o aspirador aparecer sempre como "Error" mesmo quando está na base e totalmente carregado.

Além disso, a categoria `sd` em `vacuums.py` configura automaticamente `fault_dp` para todos os robôs aspiradores. Isso significa que qualquer usuário com Cloud API configurada e um bitfield de falha informativo não zero encontra esse bug automaticamente.

#### Por que isso é seguro para todos os usuários de vacuum

A própria especificação da Tuya para a categoria `sd` inclui `in_trouble` como valor explícito do DPS de status para condições de erro. O DPS de status é a fonte autoritativa do estado de atividade do aspirador; o DPS de falha descreve qual é a falha, não necessariamente que uma falha existe.

Depois desta mudança:
- O valor de falha ainda é armazenado em `self._attrs[FAULT]` como atributo de estado.
- A entidade de sensor binário de falha não é afetada.
- Aspiradores cujo DPS de status reporta estados de erro diretamente não são afetados.
- Aspiradores com DPS de falha sempre em 0 não mudam de comportamento.
- Apenas aspiradores com bitfields informativos de falha não zero são corrigidos.

#### Arquivos alterados

- `custom_components/localtuya/vacuum.py`: remove a sobrescrita para estado `ERROR`, mantendo o valor de falha como atributo de estado.
- `custom_components/localtuya/core/ha_entities/vacuums.py`: remove `fault_dp=DPCode.FAULT` da autoconfiguração da categoria `sd`.

#### Notas de CI

A alteração em `vacuum.py` é uma remoção pura de duas linhas, sem código novo. Portanto, a formatação do `black` e o `codespell` não são afetados. Nenhuma nova cobertura de teste foi adicionada; a mudança remove uma sobrescrita incondicional em vez de introduzir nova lógica.

#### Declaração de IA

Este pull request foi desenvolvido com auxílio do agente de IA Claude.

### Commits

- `7fccae4` Remove error state assignment for fault attribute
- `df32631` fix(auto_configure): remove fault_dp from sd vacuum auto-configure

### Arquivos modificados

- `custom_components/localtuya/core/ha_entities/vacuums.py` (MODIFIED, +0/-1)
- `custom_components/localtuya/vacuum.py` (MODIFIED, +0/-2)

### Comentarios e reviews

- Comentarios: 2; Reviews: 0
  - Comentario de @xZetsubou em 2026-03-30T18:20:02Z: Thanks for the PR, But this only happen if you configured a DPS fault no? yes auto-configure do that for you but isn't this how it supposed to be works? why remove it?
  - Comentario de @t34wrj em 2026-03-31T09:02:54Z: Thanks for this. As previously disclosed, I'm relying on AI for this (which pushed me in the right direction to address the issue I was having in Home Assistant). I'll obviously leave it up to you what you do (as my configuration in Home Assistant is now working). This is the rationale (again, heavy leaning on AI): You're right that fault_dp being configured is intentional — the issue is specifically in how vacuum.py handles it. The current code does this: if self._attrs[FAULT] != 0: self._state = VacuumActivity.ERROR The problem is that on many Tuya sd vacuums (confirmed on the Lubluelu SL60D), the fault DPS is a bitfield where non-zero bits represent informational states, not actual errors. For example, bit 22 (value 4194304) means the dust collection station is connected — the vacuum is docked, fully charged, and working perfectly, but permanently shows "Error" because fault != 0. Tuya's own sd category specification includes `in_trouble` as an explicit status DPS value for genuine error conditions. This means the status DPS is the correct and authoritative source for error state — the fault DPS describes *what* the fault is, not *that* one exists. The fault value is still preserved as a state attribute and via the fault binary sensor entity — nothing is lost. We're just stopping it from unconditionally overriding the status DPS.

## PR #787: Fix/custom component bug and tools

- URL: https://github.com/xZetsubou/hass-localtuya/pull/787
- Autor: Carlo Folini (@FoliniC)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `fix/custom-component-bug-and-tools` -> `master`
- Criado em: 2026-03-16T18:53:39Z; Atualizado em: 2026-03-16T20:46:58Z
- Mudancas: +13400/-936; arquivos alterados: 58

### Descricao

O autor se coloca à disposição para ajudar a facilitar a comparação/merge deste PR. Ele acredita que a ferramenta pode ser integrada sem muitos problemas por ser independente.

#### Resumo
Este PR corrige entidades ausentes durante a configuração do LocalTuya fazendo com que os metadados de DP da Tuya Cloud sejam tratados como fonte autoritativa. Também melhora a UI do Tuya Manager com correlação mais clara entre dispositivo local e cloud, além de maior portabilidade entre instalações do Home Assistant.

#### LocalTuya: melhorias de configuração e geração de entidades
- Prioridade cloud-first para DPs: os metadados/códigos de função da Tuya Cloud passam a ser a fonte de verdade ao montar labels e mapeamentos de DP.
- A descoberta local é usada apenas como fallback.
- DPs reportados pela cloud são sempre mesclados aos DPs detectados durante a configuração, evitando criação parcial de entidades quando a descoberta local está incompleta.
- Se a geração automática não cobrir todos os DPs da cloud, o fluxo cria entidades genéricas para os `dp_ids` ausentes, mantendo todos os datapoints expostos pela cloud configuráveis.
- A mesma lógica é implementada no ConfigFlow e no OptionsFlow.
- Adiciona logs direcionados para rastrear obtenção de DPs da cloud, merge de DPs e geração de entidades.

#### Tuya Manager UI: clareza e correlação
- Exibe IP local e IP da cloud em dispositivos gerenciados e em adicionar novo dispositivo.
- Resolve MAC usando uma estratégia de melhor esforço: MAC da Tuya Cloud, campos de configuração local, e fontes LAN como ARP/neigh.
- Melhora a detecção de dispositivos já gerenciados correlacionando registros por MAC, `device_id` e `gwId`.
- Destaca dispositivos com nomes duplicados em "Add new device" e explica que nomes iguais podem representar registros de cloud diferentes.
- Mantém a UI em inglês.
- Suporta overrides por variáveis de ambiente para instalações fora de Docker: `HA_CONFIG_DIR`, `HA_CORE_CONFIG_ENTRIES_PATH`, `TUYA_GUI_SETTINGS_PATH`, `LOCALTUYA_CORE_PATH`.
- Usa a melhor opção disponível para nome: `friendly_name`, nome da cloud/local ou ID como fallback.

#### Arquivos citados
- `config_flow.py`
- `switches.py`
- `tuya_gui.py`

### Commits

- `57e0295` Fix: custom component bug + add tools for device troubleshooting
- `962e684` style: reformat cloud_api.py, coordinator.py, config_flow.py to compl…
- `15e4a21` style: reformat config_flow.py to comply with black formatting (blank…
- `538b7f9` style: run black formatting across repository (auto-reformat 19 files)
- `9b7f0a0` WIP
- `85670b2` Fix translations + add CONFIG_SCHEMA
- `8e4cd22` Format with Black

### Arquivos modificados

- `custom_components/localtuya/__init__.py` (MODIFIED, +3/-0)
- `custom_components/localtuya/binary_sensor.py` (MODIFIED, +2/-1)
- `custom_components/localtuya/config_flow.py` (MODIFIED, +886/-168)
- `custom_components/localtuya/coordinator.py` (MODIFIED, +14/-5)
- `custom_components/localtuya/core/cloud_api.py` (MODIFIED, +15/-0)
- `custom_components/localtuya/core/ha_entities/__init__.py` (MODIFIED, +152/-57)
- `custom_components/localtuya/core/ha_entities/alarm_control_panels.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/binary_sensors.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/buttons.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/climates.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/covers.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/fans.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/humidifiers.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/lights.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/locks.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/numbers.py` (MODIFIED, +6/-6)
- `custom_components/localtuya/core/ha_entities/remotes.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/selects.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/sensors.py` (MODIFIED, +19/-5)
- `custom_components/localtuya/core/ha_entities/sirens.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/switches.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/vacuums.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/ha_entities/water_heaters.py` (MODIFIED, +4/-4)
- `custom_components/localtuya/core/pytuya/__init__.py` (MODIFIED, +5/-2)
- `custom_components/localtuya/cover.py` (MODIFIED, +9/-3)
- `custom_components/localtuya/manifest.json` (MODIFIED, +1/-1)
- `custom_components/localtuya/strings.json` (MODIFIED, +10/-101)
- `custom_components/localtuya/translations/en.json` (MODIFIED, +276/-272)
- `custom_components/localtuya/translations/it.json` (MODIFIED, +90/-255)
- `tools/core_freeze/__init__.py` (ADDED, +1/-0)
- `tools/core_freeze/cloud_api.py` (ADDED, +365/-0)
- `tools/core_freeze/ha_entities/__init__.py` (ADDED, +300/-0)
- `tools/core_freeze/ha_entities/alarm_control_panels.py` (ADDED, +48/-0)
- `tools/core_freeze/ha_entities/base.py` (ADDED, +897/-0)
- `tools/core_freeze/ha_entities/binary_sensors.py` (ADDED, +492/-0)
- `tools/core_freeze/ha_entities/buttons.py` (ADDED, +251/-0)
- `tools/core_freeze/ha_entities/climates.py` (ADDED, +267/-0)
- `tools/core_freeze/ha_entities/covers.py` (ADDED, +144/-0)
- `tools/core_freeze/ha_entities/fans.py` (ADDED, +87/-0)
- `tools/core_freeze/ha_entities/humidifiers.py` (ADDED, +84/-0)
- `tools/core_freeze/ha_entities/lights.py` (ADDED, +431/-0)
- `tools/core_freeze/ha_entities/locks.py` (ADDED, +32/-0)
- `tools/core_freeze/ha_entities/numbers.py` (ADDED, +1097/-0)
- `tools/core_freeze/ha_entities/remotes.py` (ADDED, +31/-0)
- `tools/core_freeze/ha_entities/selects.py` (ADDED, +1543/-0)
- `tools/core_freeze/ha_entities/sensors.py` (ADDED, +1907/-0)
- `tools/core_freeze/ha_entities/sirens.py` (ADDED, +34/-0)
- `tools/core_freeze/ha_entities/switches.py` (ADDED, +1040/-0)
- `tools/core_freeze/ha_entities/vacuums.py` (ADDED, +95/-0)
- `tools/core_freeze/ha_entities/water_heaters.py` (ADDED, +83/-0)
- `tools/core_freeze/helpers.py` (ADDED, +116/-0)
- `tools/core_freeze/pytuya/__init__.py` (ADDED, +1342/-0)
- `tools/core_freeze/pytuya/cipher.py` (ADDED, +77/-0)
- `tools/core_freeze/pytuya/const.py` (ADDED, +103/-0)
- `tools/core_freeze/pytuya/parser.py` (ADDED, +219/-0)
- `tools/run_tuya_gui.sh` (ADDED, +4/-0)
- `tools/stop_tuya_gui.sh` (ADDED, +4/-0)
- `tools/tuya_gui.py` (ADDED, +758/-0)

### Comentarios e reviews

- Comentarios: 0; Reviews: 0

## PR #780: 🚀 Add support for device templates and docs

- URL: https://github.com/xZetsubou/hass-localtuya/pull/780
- Autor: Carlos Alexandre (@calexandre)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `feature/user-templates` -> `master`
- Criado em: 2026-02-17T01:58:35Z; Atualizado em: 2026-02-17T09:31:44Z
- Mudancas: +256/-10; arquivos alterados: 5

### Descricao

# Descrição

Este PR atualiza a estrutura da documentação para adicionar suporte a um índice de templates de dispositivos, permitindo que usuários enviem exemplos funcionais de dispositivos.

- Adiciona uma página de catálogo para templates disponíveis com instruções.
- Cria documentação para contribuição de templates de dispositivos.
- Introduz um novo template YAML para o HTW Smart Plus Water Heater.

### Commits

- `0eb1375` Fix: Add new water heater template configuration

### Arquivos modificados

- `custom_components/localtuya/templates/htw_smart_water_heater.yaml` (ADDED, +103/-0)
- `documentation/docs/contributing_templates.md` (ADDED, +72/-0)
- `documentation/docs/devices/htw_smart_water_heater.md` (ADDED, +30/-0)
- `documentation/docs/templates_catalog.md` (ADDED, +28/-0)
- `documentation/mkdocs.yml` (MODIFIED, +23/-10)

### Comentarios e reviews

- Comentarios: 1; Reviews: 0
  - Comentario de @calexandre em 2026-02-17T09:31:44Z: @xZetsubou what are your thoughts on implementing this? I think this would be of great help for future contributions. We can build an entire device index to facilitate template contributions...

## PR #747: Added QR-Code Authentication To Cloud Via SmartLife App

- URL: https://github.com/xZetsubou/hass-localtuya/pull/747
- Autor: jsb1 (@jsb1)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `auth-dev` -> `master`
- Criado em: 2025-11-30T18:25:07Z; Atualizado em: 2025-12-10T22:11:47Z
- Mudancas: +271/-313; arquivos alterados: 5

### Descricao

Olá, este patch permite login na cloud da mesma forma que a integração oficial da Tuya faz. Isso facilita bastante para usuários finais, porque não é necessário ter uma conta de desenvolvedor.

A implementação ainda está em estágio inicial de preview. Muitas coisas estão faltando, como mapeamento correto de textos e migração de entradas. A configuração da cloud está limitada ao diálogo de opções.

Sintam-se livres para recusar este pedido. Eu só quero a opinião de vocês e algumas dicas para melhorar.

Atenciosamente,

Jörg

### Commits

- `21c9aad` clound config working
- `f452477` New Tuya Claoud Autentication via QR-Code
- `50d056d` Fix missing cloud_api variable

### Arquivos modificados

- `custom_components/localtuya/__init__.py` (MODIFIED, +18/-13)
- `custom_components/localtuya/config_flow.py` (MODIFIED, +170/-105)
- `custom_components/localtuya/const.py` (MODIFIED, +13/-0)
- `custom_components/localtuya/core/cloud_api.py` (MODIFIED, +69/-194)
- `custom_components/localtuya/manifest.json` (MODIFIED, +1/-1)

### Comentarios e reviews

- Comentarios: 1; Reviews: 0
  - Comentario de @xZetsubou em 2025-12-10T22:11:47Z: Thanks for the PR. I did check this before, I thought about implement it here it will save much time on setup, But I think I stooped due to the features that is missing, Mainly because `auto-configure entities` feature fetch more data then "device data and functions only." It also fetch endpoints such as query model and properties. Which a mass losing.

## PR #647: Add pre commit hooks to run black, codespell

- URL: https://github.com/xZetsubou/hass-localtuya/pull/647
- Autor: Daniel O'Connor (@CloCkWeRX)
- Estado: OPEN; Draft: sim; Mergeable: CONFLICTING; Review decision: nenhuma
- Branches: `pre-commit-hooks` -> `master`
- Criado em: 2025-05-06T23:33:40Z; Atualizado em: 2025-05-06T23:33:59Z
- Mudancas: +42/-0; arquivos alterados: 3

### Descricao

PR empilhado; se desejado, faça merge de https://github.com/xZetsubou/hass-localtuya/pull/646 primeiro.
Se vocês não gostam de Codespaces, mas isso for útil, o autor se dispõe a refazer em cima da `master`.

TODO: por que meu `codespell` local sai com código 0?

### Commits

- `4d380d7` Add basic devcontainer
- `3f49958` Add contributing doc
- `c542ad8` Add basic pre commit hook
- `bb4ffff` Add pre-commit hook

### Arquivos modificados

- `.devcontainer/devcontainer.json` (ADDED, +4/-0)
- `CONTRIBUTING.md` (ADDED, +27/-0)
- `contrib/pre-commit` (ADDED, +11/-0)

### Comentarios e reviews

- Comentarios: 0; Reviews: 0

## PR #645: Make energy monitoring more reliable via `add_ele`

- URL: https://github.com/xZetsubou/hass-localtuya/pull/645
- Autor: TBSniller (@TBSniller)
- Estado: OPEN; Draft: sim; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `fix/energy_monitoring` -> `master`
- Criado em: 2025-05-06T20:45:07Z; Atualizado em: 2025-05-09T17:43:30Z
- Mudancas: +53/-2; arquivos alterados: 5

### Descricao

Olá,

Este PR vem desta discussão: https://github.com/xZetsubou/hass-localtuya/discussions/507#discussioncomment-13032485 e aborda as limitações atuais na funcionalidade de monitoramento de energia.

A suposição se mostrou correta: incluir um timestamp na atualização de status da entidade `add_ele` resultante realmente aciona uma atualização da entidade.
<img src="https://github.com/user-attachments/assets/be732a10-cff2-4030-8fa5-1971012adb26" width=50% height=50%>

Essa atualização é então capturada pela integração Utility Meter, permitindo acumular corretamente os valores de consumo.
<img src="https://github.com/user-attachments/assets/76c43572-6a6a-4e31-8f62-12657b50398c" width=50% height=50%>

#### Perguntas restantes

- O que acontece se o Home Assistant estiver offline e não recebermos essa atualização de status?
  - Ainda não foi totalmente testado. Porém, o autor observou que, após uma breve indisponibilidade, as atualizações foram enviadas quando o HA voltou online.
- O que acontece se a cloud não estiver acessível?
- O intervalo de valores é de 0 a 50000, então não fica preso a 100. Podemos acionar e limpar uma atualização de status, ou adiá-la?

Aberto como draft até que essas perguntas sejam respondidas.

- - -
_Primeira vez que usei parcialmente o GitHub Copilot para fazer isso. Está funcionando, mas sinceramente não sei se todas as alterações são necessárias e se estão nos lugares certos._

### Commits

- `720aedd` add timestamp attribute for DP17 (add_ele) in electricity entity
- `8826759` update faq to inform about proper energy monitoring
- `2604feb` use 3 decimals for energy sensors

### Arquivos modificados

- `custom_components/localtuya/coordinator.py` (MODIFIED, +12/-1)
- `custom_components/localtuya/core/pytuya/__init__.py` (MODIFIED, +10/-0)
- `custom_components/localtuya/entity.py` (MODIFIED, +13/-1)
- `custom_components/localtuya/sensor.py` (MODIFIED, +11/-0)
- `documentation/docs/faq/index.md` (MODIFIED, +7/-0)

### Comentarios e reviews

- Comentarios: 5; Reviews: 2
  - Comentario de @CloCkWeRX em 2025-05-06T22:37:34Z: Could you run black/tweak the code style a bit please :)
  - Comentario de @TBSniller em 2025-05-07T17:44:54Z: There for sure is something off going on. My Tuya app is giving me other values for todays overall consumption than HA. Will look into it. For the night period I can see that also some small values like `0,007 kWh` were pushed to the cloud. //Edit: ~Seems like 16 updates arrived at HA and 44 arrived at the cloud.~ - My historical data was incorrect. Have turned on debug logging for one day and can proof that all messages were received correctly. For now it looks like we have rounding errors. The funny part is that the Tuya cloud debugging tools do the same mistake. ## Cloud ``` 2025-05-07 21:56:59 | Report | Add Electricity | 0.04 ``` ## LocalTuya ``` Deciphered data = '{"protocol":4,"t":1746651419,"data":{"dps":{"17":35}}}' Entity Electricity - Additional attributes: {'raw_state': 0.04} ``` Tuya Life App displays the correct value of `0,035 kWh`
  - Comentario de @TBSniller em 2025-05-08T22:41:23Z: This change seems to work - HA now gets more precise values. Will look into it if it will be reliable ![image](https://github.com/user-attachments/assets/9ccfb4f1-27d9-4e38-9f20-431002ba45ea) ``` 2025-05-09 00:38:27.048 DEBUG (MainThread) [custom_components.localtuya.sensor] [bf5...duq - strom-04] Entity Electricity - Additional attributes: {'raw_state': 0.001} 2025-05-09 00:38:46.795 DEBUG (MainThread) [custom_components.localtuya.sensor] [bfb...y7r - strom-05] Entity Electricity - Additional attributes: {'raw_state': 0.1} 2025-05-09 00:38:46.889 DEBUG (MainThread) [custom_components.localtuya.sensor] [bfd...nzn - strom-06] Entity Electricity - Additional attributes: {'raw_state': 0.003} 2025-05-09 00:39:06.763 DEBUG (MainThread) [custom_components.localtuya.sensor] [bfb...y7r - strom-05] Entity Electricity - Additional attributes: {'raw_state': 0.1} 2025-05-09 00:39:06.971 DEBUG (MainThread) [custom_components.localtuya.sensor] [bfd...nzn - strom-06] Entity Electricity - Additional attributes: {'raw_state': 0.003} 2025-05-09 00:39:07.067 DEBUG (MainThread) [custom_components.localtuya.sensor] [bf5...duq - strom-04] Entity Electricity - Additional attributes: {'raw_state': 0.001} 2025-05-09 00:39:26.818 DEBUG (MainThread) [custom_components.localtuya.sensor] [bfb...y7r - strom-05] Entity Electricity - Additional attributes: {'raw_state': 0.1} 2025-05-09 00:39:26.923 DEBUG (MainThread) [custom_components.localtuya.sensor] [bfd...nzn - strom-06] Entity Electricity - Additional attributes: {'raw_state': 0.003} 2025-05-09 00:39:27.041 DEBUG (MainThread) [custom_components.localtuya.sensor] [bf5...duq - strom-04] Entity Electricity - Additional attributes: {'raw_state': 0.001} 2025-05-09 00:39:46.896 DEBUG (MainThread) [custom_components.localtuya.sensor] [bfd...nzn - strom-06] Entity Electricity - Additional attributes: {'raw_state': 0.003} 2025-05-09 00:39:46.907 DEBUG (MainThread) [custom_components.localtuya.sensor] [bfb...y7r - strom-05] Entity Electricity - Additional attributes: {'raw_state': 0.1} 2025-05-09 00:39:46.995 DEBUG (MainThread) [custom_components.localtuya.sensor] [bf5...duq - strom-04] Entity Electricity - Additional attributes: {'raw_state': 0.001} ```
  - Comentario de @xZetsubou em 2025-05-09T02:31:04Z: Thanks for the PR, Some of the changes is confusing the code to be honest -- but I got what are you trying to achieve 😸 I have an old local branch for this issue but again I didn't give it much time since I don't monitor my consumption 😓 In the local branch I used `state_class equal to TOTAL_INCREASING` to increase sensor value instead of replace old value, but it doesn't reset. Your PR also gave me a hint to use "update timestamp / DP" however this need a change in core module without affect the way it currently working; so we don't want to make a conditions for specific DP. We want to avoid using HA helpers to fix this. The status request will report the `add_ele` DP with timestamp so if we reload integration it will increase old value no?
  - Comentario de @TBSniller em 2025-05-09T09:31:35Z: Thanks for checking it, yeah I understand - I'm not an experienced coder at all, but I'm very willing to learn. Would appreciate it, if you could tell me what I need to change to get the code clean. Changing it to `TOTAL_INCREASING` was also my first guess, but apparently the main issue was that we have not processed all incoming values and that this is not how this attribute is working. I also thought about this, because this makes a hard coded change for this specific DP. Also was thinking about the possibility to create an option `Enable timestamp retrieval` in DP configuration and just make it default for DP 17. Would this approach suite more for you? Because I think it would be not good to always store the timestamp for all DPs, as it could blow the database with unneeded information. That we can not build it directly into the integration has also left a not nice feeling for me, because it leaves some manual doing for the user. But from my research this is the currently only "good" way to go that I have found. Otherwise we would need to copy the whole Utility Meter logic into this integration. Or we would need to create the Utility Meter helper from this integration which is a bad practice due to possible internal API changes. I think the main issue is that we only get the `add_ele` value, which we now process the same way like Tuya Cloud. Tuya Cloud also has *another* statistics endpoint, which combines the `add_ele` and timestamp values for Hour/Today/Week/Month/Year like the Utility Meter helper does. > The status request will report the add_ele DP with timestamp so if we reload integration it will increase old value no? ~I'm not 100% sure now, will check in the evening. I would assume no, as we process only incoming values, no?~ - ´Checked it, very good observation! Reloading the integration indeed pushes the value again to the Utility Meeter counter.. ~As for now this PR is working.~ At least the values are the same like Tuya gives me in their app
  - Review de @CloCkWeRX em 2025-05-06T22:44:10Z: COMMENTED
  - Review de @TBSniller em 2025-05-07T17:28:36Z: COMMENTED

## PR #619: feat: cover position scale via @nistei

- URL: https://github.com/xZetsubou/hass-localtuya/pull/619
- Autor: Daniel O'Connor (@CloCkWeRX)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `nistei/feat-cover-scale-factor` -> `master`
- Criado em: 2025-03-25T10:22:47Z; Atualizado em: 2025-05-08T08:20:29Z
- Mudancas: +22/-4; arquivos alterados: 5

### Descricao

Uma versão de https://github.com/rospogrigio/localtuya/pull/1755 para este repositório.

@nistei, vi seu PR no repositório principal e, como este fork é muito mais mantido, achei que valia a pena trazer a mudança para cá.

### Commits

- `f3fefee` feat: cover position scale via @nistei
- `00c9247` Fix merge error
- `58d942e` Run black.
- `8eb14da` Refactor slightly to avoid ever returning a position scale of 0
- `8539601` Merge remote-tracking branch 'xZetsubou/master' into nistei/feat-cove…

### Arquivos modificados

- `custom_components/localtuya/const.py` (MODIFIED, +1/-0)
- `custom_components/localtuya/cover.py` (MODIFIED, +18/-2)
- `custom_components/localtuya/strings.json` (MODIFIED, +1/-0)
- `custom_components/localtuya/translations/it.json` (MODIFIED, +1/-1)
- `custom_components/localtuya/translations/pt-BR.json` (MODIFIED, +1/-1)

### Comentarios e reviews

- Comentarios: 1; Reviews: 1
  - Comentario de @CloCkWeRX em 2025-05-06T23:04:46Z: Should be good to go
  - Review de @xZetsubou em 2025-05-08T08:20:29Z: COMMENTED: Thanks for the PR

## PR #618: Fix for BLE Lights that behaves weird when sending the entire state

- URL: https://github.com/xZetsubou/hass-localtuya/pull/618
- Autor: Daniel O'Connor (@CloCkWeRX)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `ble-lights-pr` -> `master`
- Criado em: 2025-03-25T09:55:23Z; Atualizado em: 2025-03-25T10:27:13Z
- Mudancas: +39/-1; arquivos alterados: 2

### Descricao

Era o PR https://github.com/xZetsubou/hass-localtuya/pull/603; este apenas limpa os outros arquivos.

### Commits

- `3e3eef9` Add a version of https://github.com/xZetsubou/hass-localtuya/pull/603
- `d8ba81c` Update custom_components/localtuya/coordinator.py
- `b20b811` Black

### Arquivos modificados

- `custom_components/localtuya/coordinator.py` (MODIFIED, +9/-0)
- `custom_components/localtuya/light.py` (MODIFIED, +30/-1)

### Comentarios e reviews

- Comentarios: 0; Reviews: 1
  - Review de @CloCkWeRX em 2025-03-25T09:55:38Z: COMMENTED

## PR #603: Fix for BLE Lights that behaves weird when sending the entire state

- URL: https://github.com/xZetsubou/hass-localtuya/pull/603
- Autor: Xferno2 (@Xferno2)
- Estado: OPEN; Draft: nao; Mergeable: MERGEABLE; Review decision: nenhuma
- Branches: `master` -> `master`
- Criado em: 2025-03-11T13:15:49Z; Atualizado em: 2026-02-28T19:52:03Z
- Mudancas: +559/-3; arquivos alterados: 7

### Descricao

Olá, se já existe uma forma de corrigir isso e eu não encontrei, por favor fechem este PR.

Tenho várias lâmpadas BLE baratas que, quando estão no modo de trabalho "white", recusam o estado completo, mesmo com manual DP 0, se ele não for enviado um por um. Adicionei outro manual DP, `-10`, para corrigir isso. Eu comparo com os dados em cache para não enviar estados em excesso; se o estado do DP for o mesmo, ele não é reenviado.

Fiz isso principalmente porque, no modo de temperatura pelo HA, elas recusavam qualquer comando.

Espero que isso não quebre compatibilidade com outros dispositivos de luz. Não consigo testar em outros porque não tenho nenhum.

### Commits

- `ea2b2cc` Testing implemantation for weird sending one state lights
- `9db4cc5` Refactoring
- `67410a7` Fixed set dps for other states
- `5593a37` Trying to fix all statess
- `37e329b` .
- `633c6f0` Maybe fixed
- `1ba54c6` ..
- `d5c7765` testing
- `e6fe74f` Hopefully mapped correct the states now
- `2143d27` Maybe fix for brightness
- `0935862` I have no clue what im doing at this point
- `d714da3` Checking so the values are not None when sending commands
- `c9867e1` Made color_temp default as None
- `9d81aca` Maybe fix for color brigness
- `45d798a` trying to fix colors
- `fb298d8` Update only the changed value not all of the states so it doesn't spa…
- `599c673` Made last state atributes only for send one state devices. Rename tem…
- `4ddc308` If it's the first command then return None for last states
- `8b607c6` Added try and catch to last values.
- `fa35847` Thread blocking
- `c94105f` Hopefully fixed last states
- `5cdd328` Reverted Changes
- `4fdd01e` Trying to remove the bug when switching from temp to color
- `1e33fb2` attemp 2
- `c93749e` maybe fix
- `6585b8a` attempt 4
- `d0598a6` attemp 5
- `413ad79` attemp 6
- `b7fd2aa` attemp 7
- `eb71311` attempt 8
- `b4a07b8` Clean up
- `9a0c942` Merge pull request #1 from xZetsubou/master
- `5817db0` Update Git Ignore
- `98e7aec` Merge branch 'master' of https://github.com/Xferno2/hass-localtuya
- `dffac46` Delete .vs directory
- `8826246` Merge pull request #2 from xZetsubou/master
- `25aadb4` Turn on light if temperature changes.
- `dd8a9c9` Turn on lights on temp change
- `1240040` Check if light is already on
- `d5a5ebc` Merge pull request #3 from xZetsubou/master
- `7b9b92d` Fixed typo and added black style format
- `2761eea` Merge branch 'master' of https://github.com/Xferno2/hass-localtuya
- `b4b208a` Merge branch 'xZetsubou:master' into master
- `4815046` Merge branch 'xZetsubou:master' into master
- `3c31e06` Merge branch 'xZetsubou:master' into master
- `3c8ba09` Merge branch 'xZetsubou:master' into master
- `1b0e072` Merge branch 'xZetsubou:master' into master
- `229947c` Merge branch 'xZetsubou:master' into master
- `3155a69` Merge branch 'xZetsubou:master' into master
- `8700e8d` Merge branch 'xZetsubou:master' into master
- `ac62319` Merge branch 'xZetsubou:master' into master
- `808682c` Merge branch 'xZetsubou:master' into master
- `4ca9420` Merge branch 'xZetsubou:master' into master
- `e01dabf` Merge branch 'xZetsubou:master' into master
- `1710fe5` Merge branch 'xZetsubou:master' into master

### Arquivos modificados

- `.gitignore` (MODIFIED, +337/-2)
- `.vs/hass-localtuya/v17/.wsuo` (ADDED, +0/-0)
- `.vs/hass-localtuya/v17/DocumentLayout.backup.json` (ADDED, +92/-0)
- `.vs/hass-localtuya/v17/DocumentLayout.json` (ADDED, +91/-0)
- `.vs/slnx.sqlite` (ADDED, +0/-0)
- `custom_components/localtuya/coordinator.py` (MODIFIED, +9/-0)
- `custom_components/localtuya/light.py` (MODIFIED, +30/-1)

### Comentarios e reviews

- Comentarios: 5; Reviews: 0
  - Comentario de @CloCkWeRX em 2025-03-25T05:49:22Z: Thanks for having a go at this! So, you have a few extra bits and pieces in this PR, meaning it can't be merged as is. First step would be to create a new feature branch, and just add your changes to coordinator.py and light.py If you like, I can do this on your behalf in a few hours.
  - Comentario de @Xferno2 em 2025-03-25T07:35:35Z: Hello, I'm not exactly sure how to do that. I created a new branch in my repo project but I'm not sure how to change it in the PR request. So if you could do it on my behalf I would appreciate it. I should really learn how to use github at some point.
  - Comentario de @CloCkWeRX em 2025-03-25T08:08:42Z: No worries. Provided I don't forget it'll be a few hours from now. For how to on the command line: https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging Or basically 'git checkout -b fix-xyz' GitHub equivalent: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-and-deleting-branches-within-your-repository There's a few more around `git rm` or `git add` that are worth diving a bit deeper into with specific file paths; some stuff around maybe a .gitignore file to make life easier - but once you have that under your belt you are on par with the a lot of git users!
  - Comentario de @CloCkWeRX em 2025-03-25T09:56:22Z: Okay; https://github.com/xZetsubou/hass-localtuya/pull/618/files is raised. There might be other feedback before its mergable, but it's a step closer :)
  - Comentario de @xZetsubou em 2025-03-28T06:10:03Z: Sorry for late reply, and thanks for the PR. Manual DPS isn't used to affect a type of entities e,g, "lights" this field is for device generally e.g. `0` = ignore device handshake or `-1` = low-power device. Another thing is that this behavior may not be normal and it may be hardware issue? If you setup the cloud with localtuya can you post the device diagnostics if not then post model query from Tuya IoT


# Analise de merge dos PRs abertos

Repo: `xZetsubou/hass-localtuya`  
Base analisada: `master` local  
Branches locais: `pr-603`, `pr-618`, `pr-619`, `pr-645`, `pr-647`, `pr-747`, `pr-780`, `pr-787`, `pr-790`, `pr-792`, `pr-794`, `pr-796`, `pr-802`, `pr-806`, `pr-807`, `pr-809`, `pr-815`

## Resumo executivo

### Bons candidatos para merge direto ou quase direto

- `pr-802` - Corrige fator de conversao de profundidade liquida. Muito pequeno, baixo risco.
- `pr-792` - Respeita `fan_dps_type` ao enviar velocidade do fan. Pequeno, baixo risco.
- `pr-790` - Remove estado `ERROR` automatico de vacuum baseado em `fault_dp`. Pequeno e faz sentido.
- `pr-809` - Corrige negociacao/reconexao v3.5. Pequeno, mas precisa teste real em device v3.5.
- `pr-806` - Normaliza `EntityCategory.CONFIG` para sensores/binary_sensors. Faz sentido para compatibilidade HA.
- `pr-619` - Adiciona escala de posicao para covers. Feature pequena, aceitavel com teste manual.
- `pr-815` - Adiciona `offset` para sensores/numbers e inclui teste. Bom candidato, mas conflita com `pr-645`.
- `pr-780` - Template/docs de water heater. Baixo risco para runtime, mas revisar YAML/docs.

### Bons candidatos, mas precisam ajuste antes

- `pr-807` - Opcao por dispositivo para baixar logs de "unreachable" para DEBUG. Pequeno e util, mas conflita com `pr-794`.
- `pr-794` - Suporte a device low-power event-driven, com testes. Boa ideia, mas mexe em fluxo de conexao/keepalive; precisa validar com hardware e resolver conflito com `pr-807`.
- `pr-796` - Expoe service `update_dps`. Util, mas usa `device._interface` privado e engole `TimeoutError`; eu ajustaria antes.
- `pr-645` - Energia via `add_ele`/timestamp. Ideia util, mas hardcode em DP `17`, muda rounding para energia e conflita com `pr-815`.
- `pr-618` - Versao limpa do fix de BLE lights do `pr-603`. Pode ser considerado, mas usa sentinel `-10` em manual DPS e precisa documentacao/teste.

### Nao mergear direto

- `pr-603` - Mesma ideia util do `pr-618`, mas inclui arquivos `.vs` e muito ruido. Preferir `pr-618`.
- `pr-647` - Pre-commit/devcontainer. Ja conflita com arquivos existentes em `master`; hook e docs precisam ser refeitos em cima do estado atual.
- `pr-747` - Troca grande do modelo de Cloud API para QR/auth via SDK. Pode ser valioso, mas e migracao grande e potencialmente breaking.
- `pr-787` - PR enorme com WIP, logs `[TRACER]`, ferramentas novas e varias mudancas misturadas. Nao mergear como esta; extrair patches especificos.

## Conflitos automaticos encontrados

- Contra `master`: `pr-647` conflita em `.devcontainer/devcontainer.json` e `CONTRIBUTING.md`.
- Entre candidatos:
  - `pr-794` x `pr-807`: ambos mexem em `config_flow.py`, `const.py`, `coordinator.py`, `translations/en.json`.
  - `pr-815` x `pr-645`: ambos mexem em `entity.scale()` e area de sensor/coordinator.
- `pr-603` e `pr-618` tem o mesmo patch util para `coordinator.py`/`light.py` pelo `git patch-id`; `pr-618` e a versao limpa.

## Ordem sugerida

1. Mergear pequenos independentes primeiro:
   `pr-802`, `pr-792`, `pr-790`, `pr-809`, `pr-806`, `pr-619`.
2. Mergear `pr-780` se o objetivo incluir catalogo/templates no repo.
3. Mergear `pr-815` antes de `pr-645`, porque tem teste e implementa transformacao generica `value * scaling + offset`.
4. Rebase/adaptar `pr-645` por cima de `pr-815`, mantendo timestamp de DP `17`, mas revisando hardcode e rounding.
5. Resolver manualmente `pr-794` + `pr-807`; os dois fazem sentido, mas a combinacao precisa preservar as duas opcoes no schema.
6. Avaliar `pr-796` com pequenos ajustes de robustez antes de merge.
7. Avaliar `pr-618` separadamente, com documentacao do sentinel `-10` ou uma opcao de config explicita.
8. Nao mergear `pr-603`, `pr-647`, `pr-747`, `pr-787` diretamente.

## Analise por PR

### PR 815 - Add constant offset to sensor values

Recomendacao: mergear, com atencao ao conflito com `pr-645`.

O PR adiciona `CONF_OFFSET` e aplica a formula `value * scaling + offset` para leitura, alem de desfazer offset/scaling ao escrever numbers. O detalhe bom e que `step_size` usa apenas scaling, sem offset. Tambem adiciona teste em `tests/test_number.py`.

Risco: a mudanca central fica em `LocalTuyaEntity.scale()`, entao qualquer PR que mexa em scaling precisa ser integrado com cuidado.

### PR 809 - v3.5 session key negotiation failures on reconnect

Recomendacao: mergear apos teste real com device v3.5.

Corrige `clean_up_session()` para restaurar `local_key` a partir de `real_local_key`, atualiza `dispatcher.local_key` antes de negociar e permite que `ConnectionAbortedError` continue tentando outras versoes no auto protocol.

Risco: baixo no diff, mas area sensivel de protocolo.

### PR 807 - Per device logging

Recomendacao: mergear junto ou depois de resolver com `pr-794`.

Adiciona `debug_unreachable_errors` por dispositivo para reduzir log warning de falhas de conexao esperadas. E util para dispositivos que dormem ou ficam intermitentes.

Risco: baixo. Conflita com `pr-794` porque ambos adicionam opcoes no mesmo schema/config.

### PR 806 - Change some entities from config to diagnostic

Recomendacao: mergear.

Evita que sensores e binary_sensors recebam `EntityCategory.CONFIG`, normalizando para `DIAGNOSTIC` quando necessario. Isso parece alinhado com restricoes recentes do Home Assistant.

Risco: baixo/medio, porque muda comportamento de entidades antigas; mas a alternativa e quebrar configuracoes invalidas.

### PR 802 - Liquid depth scale factor

Recomendacao: mergear.

Muda profundidade liquida de escala `1` para `0.01`. Diff minimo.

Risco: baixo, assumindo que o DP vem em centimetros/centimos.

### PR 796 - Expose update_dps service

Recomendacao: ajustar antes de merge.

Adiciona service `localtuya.update_dps` para pedir refresh de DPs. Feature util para debug e dispositivos especificos.

Riscos/ajustes:
- usa `device._interface` e `device._node_id`, ambos privados;
- ignora `TimeoutError` silenciosamente;
- schema `dps: list` poderia validar melhor os itens;
- deveria retornar erro claro se interface nao existir.

### PR 794 - Event-driven low-power support

Recomendacao: bom candidato, mas nao mergear sem validar.

Adiciona opcao `device_event_driven`, trata o dispositivo como low-power sempre, pula refresh/keepalive e adiciona testes.

Riscos:
- altera fluxo de conexao e disponibilidade;
- `is_sleep` passa a ter efeito colateral (`setattr(self, "low_power", True)`);
- precisa teste real com sensores que acordam por evento.

### PR 792 - Fan dps type string

Recomendacao: mergear.

Ao controlar velocidade por range, converte o valor para string quando `CONF_FAN_DPS_TYPE == "str"`. Pequeno e coerente com o nome da opcao.

Risco: baixo.

### PR 790 - Vacuum fault_dp error override

Recomendacao: mergear.

Remove `fault_dp` do auto-config para um modelo e para de forcar estado `ERROR` quando fault != 0, mantendo o fault como atributo.

Risco: baixo/medio. Pode mudar comportamento para usuarios que gostavam do erro automatico, mas evita falso positivo reportado.

### PR 787 - Fix/custom component bug and tools

Recomendacao: nao mergear direto.

PR enorme: 58 arquivos, 13k linhas adicionadas, tools novos, core freeze, alteracoes em config flow, cloud api, translations e protocolo. Encontrei logs `[TRACER]`, comentarios WIP e mudancas muito especificas.

Possiveis partes para extrair:
- `CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)`;
- comandos de cover `True_True_True`, se houver issue/device justificando;
- guard `curr_pos is not None` antes de inverter posicao.

### PR 780 - Device templates and docs

Recomendacao: mergear se o projeto quer comecar catalogo de templates.

Adiciona template YAML de HTW Smart Plus Water Heater e paginas de docs/catalogo.

Risco: baixo para runtime. Revisar:
- link externo no comentario do YAML;
- unidades `ºC` vs padrao HA;
- se docs querem esse novo catalogo agora.

### PR 747 - QR-Code Authentication To Cloud Via SmartLife App

Recomendacao: nao mergear direto; tratar como projeto separado.

Troca auth por client/secret/user_id para QR login via `tuya-device-sharing-sdk`, muda `TuyaCloudApi`, config flow e dados persistidos.

Riscos:
- migracao de entradas existentes;
- dependencia nova;
- muda completamente fluxo cloud;
- precisa testes e plano de fallback/no-cloud.

### PR 647 - Pre-commit hooks

Recomendacao: nao mergear como esta.

Conflita com `.devcontainer/devcontainer.json` e `CONTRIBUTING.md` ja existentes. O hook usa `grep ".py"` e executa `black` em arquivos staged, podendo alterar staging sem avisar.

Melhor refazer usando `.pre-commit-config.yaml` padrao.

### PR 645 - Energy monitoring via add_ele

Recomendacao: adaptar antes de merge.

Armazena timestamp para DP `17`, expoe atributo `timestamp` para sensor de energia e usa 3 casas decimais para energia.

Riscos:
- DP `17` hardcoded;
- `extra_state_attributes` pode conflitar com atributos existentes se nao copiar corretamente;
- conflito com `pr-815` na funcao `scale()`;
- precisa teste para payload `dps` com `t`.

### PR 619 - Cover position scale

Recomendacao: mergear com teste manual.

Adiciona `position_scale` para cover, usado tanto ao ler quanto ao setar posicao.

Risco: baixo/medio. Seria bom adicionar teste de escala e inversao.

### PR 618 - BLE lights send one state

Recomendacao: considerar depois, preferindo `pr-618` sobre `pr-603`.

Corrige devices BLE que nao aceitam payload completo, enviando DPs individuais em modo branco. Usa `-10` em manual DPS como marcador.

Riscos:
- sentinel `-10` e pouco descobrivel e sem doc;
- comentario tem typo e sem teste;
- comportamento especifico de light pode afetar atualizacoes de brilho/temp.

### PR 603 - BLE lights original

Recomendacao: nao mergear.

Mesmo patch util do `pr-618`, mas com arquivos `.vs`, `.gitignore` enorme e historico ruidoso.

### Combinacao 815 + 645

Recomendacao: aplicar `815` primeiro. Depois adaptar `645` para manter:

```python
value = value * scale_factor
if not scale_only and offset is not None:
    value = value + offset
precision = 3 if device_class == "energy" else 2
value = round(value, precision)
```

Isso preserva offset e rounding especial.

### Combinacao 794 + 807

Recomendacao: resolver manualmente mantendo ambos os campos:

- `CONF_DEVICE_EVENT_DRIVEN`
- `CONF_DEBUG_UNREACHABLE_ERRORS`

Ambos precisam aparecer em `DEVICE_SCHEMA`, `options_schema`, `DeviceConfig`, translations e nos defaults criados por cloud setup.

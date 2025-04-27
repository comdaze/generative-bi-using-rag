import { Divider, Heading } from "@aws-amplify/ui-react";
import {
  Button,
  Drawer,
  FormField,
  Grid,
  Input,
  Select,
  Slider,
  SpaceBetween,
  Toggle,
} from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useDispatch, useSelector } from "react-redux";
import { getSelectData } from "../../utils/api/API";
import {
  ActionType,
  LLMConfigState,
  UserState,
} from "../../utils/helpers/types";
import { useI18n } from "../../utils/i18n";
import "./style.scss";

const PanelConfigs = ({
  setToolsHide,
}: {
  setToolsHide: Dispatch<SetStateAction<boolean>>;
}) => {
  const dispatch = useDispatch();
  const queryConfig = useSelector((state: UserState) => state.queryConfig);
  const { t } = useI18n();

  const [intentChecked, setIntentChecked] = useState(queryConfig.intentChecked);
  const [complexChecked, setComplexChecked] = useState(
    queryConfig.complexChecked
  );
  const [answerInsightChecked, setAnswerInsightChecked] = useState(
    queryConfig.answerInsightChecked
  );
  const [contextWindow, setContextWindow] = useState(queryConfig.contextWindow);
  const [modelSuggestChecked, setModelSuggestChecked] = useState(
    queryConfig.modelSuggestChecked
  );
  const [temperature, setTemperature] = useState(queryConfig.temperature);
  const [topP, setTopP] = useState(queryConfig.topP);
  const [topK, setTopK] = useState(queryConfig.topK);
  const [maxLength, setMaxLength] = useState(queryConfig.maxLength);
  const [llmOptions, setLLMOptions] = useState([] as any[]);
  const [dataProOptions, setDataProOptions] = useState([] as any[]);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [selectedLLM, setSelectedLLM] = useState({
    label: queryConfig.selectedLLM,
    value: queryConfig.selectedLLM,
  } as any);
  const [selectedDataPro, setSelectedDataPro] = useState({
    label: queryConfig.selectedDataPro,
    value: queryConfig.selectedDataPro,
  } as any);

  useEffect(() => {
    setLoadingProfile(true);
    try {
      getSelectData().then((response) => {
        const tempLLM: SetStateAction<null> | { label: any; value: any }[] = [];
        response.bedrock_model_ids?.forEach((item: any) => {
          tempLLM.push({ label: item, value: item });
        });
        setLLMOptions(tempLLM);
        if (!queryConfig?.selectedLLM) {
          setSelectedLLM(tempLLM[0]);
          toast.success(`Now using LLM: ${tempLLM[0]}`);
        }

        const tempDataPro: SetStateAction<null> | { label: any; value: any }[] =
          [];
        response.data_profiles?.forEach((item: any) => {
          tempDataPro.push({ label: item, value: item });
        });
        setDataProOptions(tempDataPro);
        if (!queryConfig?.selectedDataPro) {
          setSelectedDataPro(tempDataPro[0]);
          toast.success(`Now viewing data profile: ${tempDataPro[0]}`);
        }
      });
    } catch (error) {
      console.warn("getSelectData error in useEffect: ", error);
    } finally {
      setLoadingProfile(false);
    }
  }, [queryConfig?.selectedDataPro, queryConfig?.selectedLLM]);

  useEffect(() => {
    const configInfo: LLMConfigState = {
      selectedLLM: selectedLLM ? selectedLLM.value : "",
      selectedDataPro: selectedDataPro ? selectedDataPro.value : "",
      intentChecked,
      complexChecked,
      answerInsightChecked,
      contextWindow,
      modelSuggestChecked,
      temperature,
      topP,
      topK,
      maxLength,
    };
    dispatch({ type: ActionType.UpdateConfig, state: configInfo });
  }, [
    selectedLLM,
    selectedDataPro,
    intentChecked,
    complexChecked,
    answerInsightChecked,
    modelSuggestChecked,
    temperature,
    topP,
    topK,
    maxLength,
    contextWindow,
    dispatch,
  ]);

  // 监听语言变化，强制重新渲染
  const [, forceUpdate] = useState({});
  useEffect(() => {
    const handleLanguageChange = () => {
      forceUpdate({});
    };
    
    window.addEventListener('languageChanged', handleLanguageChange);
    return () => {
      window.removeEventListener('languageChanged', handleLanguageChange);
    };
  }, []);

  return (
    <Drawer header={t('configs.configurations')}>
      <SpaceBetween size="xxl">
        <SpaceBetween size="m">
          <FormField label={t('configs.llmModel')}>
            <Select
              options={llmOptions}
              selectedOption={selectedLLM}
              loadingText={t('configs.loadingModels')}
              statusType={loadingProfile ? "loading" : "finished"}
              onChange={({ detail }) => setSelectedLLM(detail.selectedOption)}
            />
          </FormField>
          <FormField label={t('configs.dataProfile')}>
            <Select
              options={dataProOptions}
              loadingText={t('configs.loadingProfiles')}
              statusType={loadingProfile ? "loading" : "finished"}
              selectedOption={selectedDataPro}
              onChange={({ detail }) => {
                const newProfile = detail.selectedOption;
                setSelectedDataPro(newProfile);
                toast.success(
                  <div>
                    {t('configs.nowViewingProfile')}
                    <Heading>
                      <em>{newProfile.value}</em>
                    </Heading>
                  </div>
                );
              }}
            />
          </FormField>
        </SpaceBetween>

        <Divider label={t('configs.queryConfig')} />

        <SpaceBetween size="s">
          <Toggle
            onChange={({ detail }) => setIntentChecked(detail.checked)}
            checked={intentChecked}
          >
            {t('configs.intentRecognition')}
          </Toggle>
          <Toggle
            onChange={({ detail }) => setComplexChecked(detail.checked)}
            checked={complexChecked}
          >
            {t('configs.complexQuery')}
          </Toggle>
          <Toggle
            onChange={({ detail }) => setModelSuggestChecked(detail.checked)}
            checked={modelSuggestChecked}
          >
            {t('configs.modelSuggestion')}
          </Toggle>
          <Toggle
            onChange={({ detail }) => setAnswerInsightChecked(detail.checked)}
            checked={answerInsightChecked}
          >
            {t('configs.answerWithInsights')}
          </Toggle>
          <div style={{ height: "3px" }} />
          <FormField label={t('configs.contextWindow')}>
            <div className="input-wrapper">
              <Input
                type="number"
                inputMode="numeric"
                value={contextWindow?.toString()}
                onChange={({ detail }) => {
                  if (Number(detail.value) > 10 || Number(detail.value) < 0) {
                    return;
                  }
                  setContextWindow(Number(detail.value));
                }}
                controlId="maxlength-input"
                step={1}
              />
            </div>
            <div className="flex-wrapper">
              <div className="slider-wrapper">
                <Slider
                  onChange={({ detail }) => setContextWindow(detail.value)}
                  value={contextWindow}
                  max={10}
                  min={0}
                  step={1}
                />
              </div>
            </div>
          </FormField>
        </SpaceBetween>

        <Divider label={t('configs.modelConfig')} />

        <SpaceBetween size="xs">
          <Grid
            gridDefinition={[
              { colspan: { default: 6, xxs: 12 } },
              { colspan: { default: 1, xxs: 0 } },
              { colspan: { default: 5, xxs: 12 } },
            ]}
          >
            <FormField label={t('configs.temperature')}>
              <div className="input-wrapper">
                <Input
                  type="number"
                  inputMode="decimal"
                  value={temperature?.toString()}
                  onChange={({ detail }) => {
                    if (Number(detail.value) > 1 || Number(detail.value) < 0) {
                      return;
                    }
                    setTemperature(Number(detail.value));
                  }}
                  controlId="temperature-input"
                  step={0.1}
                />
              </div>
              <div className="flex-wrapper">
                <div className="slider-wrapper">
                  <Slider
                    onChange={({ detail }) => setTemperature(detail.value)}
                    value={temperature}
                    max={1}
                    min={0}
                    step={0.1}
                    valueFormatter={(e) => e.toFixed(1)}
                  />
                </div>
              </div>
            </FormField>

            <VerticalDivider />

            <FormField label={t('configs.topP')}>
              <div className="input-wrapper">
                <Input
                  type="number"
                  inputMode="numeric"
                  value={topP?.toString()}
                  onChange={({ detail }) => {
                    if (Number(detail.value) > 1 || Number(detail.value) < 0) {
                      return;
                    }
                    setTopP(Number(detail.value));
                  }}
                  controlId="top-input"
                  step={0.001}
                />
              </div>
              <div className="flex-wrapper">
                <div className="slider-wrapper">
                  <Slider
                    onChange={({ detail }) => setTopP(detail.value)}
                    value={topP}
                    max={1}
                    min={0}
                    step={0.001}
                    valueFormatter={(e) => e.toFixed(3)}
                  />
                </div>
              </div>
            </FormField>
          </Grid>

          <Grid
            gridDefinition={[
              { colspan: { default: 6, xxs: 12 } },
              { colspan: { default: 1, xxs: 0 } },
              { colspan: { default: 5, xxs: 12 } },
            ]}
          >
            <FormField label={t('configs.maxLength')}>
              <div className="input-wrapper">
                <Input
                  type="number"
                  inputMode="numeric"
                  value={maxLength?.toString()}
                  onChange={({ detail }) => {
                    if (
                      Number(detail.value) > 2048 ||
                      Number(detail.value) < 1
                    ) {
                      return;
                    }
                    setMaxLength(Number(detail.value));
                  }}
                  controlId="maxlength-input"
                  step={1}
                />
              </div>
              <div className="flex-wrapper">
                <div className="slider-wrapper">
                  <Slider
                    onChange={({ detail }) => setMaxLength(detail.value)}
                    value={maxLength}
                    max={2048}
                    min={1}
                    step={1}
                  />
                </div>
              </div>
            </FormField>

            <VerticalDivider />

            <FormField label={t('configs.topK')}>
              <div className="input-wrapper">
                <Input
                  type="number"
                  inputMode="numeric"
                  value={topK?.toString()}
                  onChange={({ detail }) => {
                    if (
                      Number(detail.value) > 500 ||
                      Number(detail.value) < 0
                    ) {
                      return;
                    }
                    setTopK(Number(detail.value));
                  }}
                  controlId="topk-input"
                  step={1}
                />
              </div>
              <div className="flex-wrapper">
                <div className="slider-wrapper">
                  <Slider
                    onChange={({ detail }) => setTopK(detail.value)}
                    value={topK}
                    max={500}
                    min={0}
                    step={1}
                  />
                </div>
              </div>
            </FormField>
          </Grid>
        </SpaceBetween>

        <Button
          variant="primary"
          iconName="status-positive"
          onClick={() => {
            const configInfo: LLMConfigState = {
              selectedLLM: selectedLLM ? selectedLLM.value : "",
              selectedDataPro: selectedDataPro ? selectedDataPro.value : "",
              intentChecked,
              complexChecked,
              answerInsightChecked,
              contextWindow,
              modelSuggestChecked,
              temperature,
              topP,
              topK,
              maxLength,
            };
            dispatch({ type: ActionType.UpdateConfig, state: configInfo });
            setToolsHide(true);
            toast.success(t('configs.configSaved'));
          }}
        >
          {t('configs.save')}
        </Button>
      </SpaceBetween>
    </Drawer>
  );
};
export default PanelConfigs;

function VerticalDivider() {
  return (
    <div
      style={{
        borderLeft: "1px solid silver",
        width: "1px",
        height: "80%",
        margin: "0 auto",
      }}
    />
  );
}

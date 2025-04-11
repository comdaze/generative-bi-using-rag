import {
  BarChart,
  Form,
  FormField,
  Grid,
  LineChart,
  PieChart,
  Select,
  SpaceBetween,
  Tabs,
} from "@cloudscape-design/components";
import React, { useMemo, useState } from "react";
import { CHART_TYPE } from "./types";

interface IPropsChartPanel {
  data_show_type: CHART_TYPE;
  sql_data: any[][];
}
const ChartPanel: React.FC<IPropsChartPanel> = ({
  data_show_type,
  sql_data,
}) => {
  const [header, ...items] = sql_data;
  const chartDataProcessed: Record<string, any[]> = useMemo(() => {
    const processedArray = header.reduce((acc, cur, i) => {
      acc[cur] = items.map((datum) => datum[i]);
      return acc;
    }, {});
    return processedArray;
  }, [header, items]);
  const axisOptions = useMemo(
    () => header.map((value) => ({ value })),
    [header]
  );
  let chartComponent = <></>;
  const [activeTabId, setActiveTabId] = useState<CHART_TYPE>(data_show_type);
  const [xColName, setXColName] = useState<string | undefined>(header[0]);
  const [yColName, setYColName] = useState<string | undefined>(header[1]);

  if (!xColName || !yColName)
    return (
      <div>
        sql_data error:
        <br />
        {sql_data}
      </div>
    );

  switch (activeTabId) {
    case CHART_TYPE.bar: {
      const seriesValue = [
        {
          title: yColName,
          type: "bar",
          data: chartDataProcessed[xColName].map((x, i) => ({
            x,
            y: chartDataProcessed[yColName][i],
          })),
        } as const,
      ];
      chartComponent = (
        <BarChart
          series={seriesValue}
          height={200}
          hideFilter
          xTitle={xColName}
          yTitle={yColName}
        />
      );
      break;
    }
    case CHART_TYPE.line: {
      const seriesValue = [
        {
          title: yColName,
          type: "line",
          data: chartDataProcessed[xColName].map((x, i) => ({
            x,
            y: chartDataProcessed[yColName][i],
          })),
        } as const,
      ];
      chartComponent = (
        <LineChart
          series={seriesValue}
          height={200}
          hideFilter
          xScaleType="categorical"
          xTitle={xColName}
          yTitle={yColName}
        />
      );
      break;
    }
    case CHART_TYPE.pie: {
      const tooManyShares = chartDataProcessed[xColName].length > 25;
      chartComponent = (
        <PieChart
          data={chartDataProcessed[xColName].map((x, i) => ({
            title: x,
            value: chartDataProcessed[yColName][i],
          }))}
          size={tooManyShares ? "large" : "medium"}
          variant={tooManyShares ? "donut" : "pie"}
          fitHeight
          hideFilter
          hideLegend
          detailPopoverContent={(datum, sum) => [
            { key: yColName, value: datum.value },
            {
              key: "Percentage",
              value: `${((datum.value / sum) * 100).toFixed(2)}%`,
            },
          ]}
        />
      );
      break;
    }
  }

  return (
    <Tabs
      activeTabId={activeTabId}
      onChange={({ detail }) =>
        setActiveTabId(detail.activeTabId as CHART_TYPE)
      }
      variant="container"
      tabs={Object.values(CHART_TYPE).map((v) => ({
        label: `${v[0].toUpperCase()}${v.substring(1).toLowerCase()} Chart`,
        id: v,
        content: (
          <SpaceBetween size="l">
            <Form>
              <Grid gridDefinition={[{ colspan: 3 }, { colspan: 3 }]}>
                <FormField
                  label={
                    activeTabId === CHART_TYPE.pie
                      ? "Choose title column"
                      : "Choose x-axis column"
                  }
                >
                  <Select
                    selectedOption={{ value: xColName }}
                    onChange={({ detail }) =>
                      setXColName(detail.selectedOption.value)
                    }
                    options={axisOptions}
                  />
                </FormField>

                <FormField
                  label={
                    activeTabId === CHART_TYPE.pie
                      ? "Choose value column"
                      : "Choose y-axis column"
                  }
                >
                  <Select
                    selectedOption={{ value: yColName }}
                    onChange={({ detail }) =>
                      setYColName(detail.selectedOption.value)
                    }
                    options={axisOptions}
                  />
                </FormField>
              </Grid>
            </Form>
            <div>{chartComponent}</div>
          </SpaceBetween>
        ),
      }))}
    />
  );
};

export default ChartPanel;

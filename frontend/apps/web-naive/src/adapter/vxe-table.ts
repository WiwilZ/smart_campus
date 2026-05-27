import type { VxeTableGridOptions } from '@vben/plugins/vxe-table';

import type { ComponentPropsMap, ComponentType } from './component';

import { h } from 'vue';

import { $t } from '@vben/locales';
import { setupVbenVxeTable, useVbenVxeGrid as useGrid } from '@vben/plugins/vxe-table';
import { isFunction, isString } from '@vben/utils';

import { NButton, NImage, NPopconfirm, NSwitch, NTag } from 'naive-ui';

import { useVbenForm } from './form';

setupVbenVxeTable({
  configVxeTable: (vxeUI) => {
    vxeUI.setConfig({
      grid: {
        align: 'center',
        border: false,
        columnConfig: {
          resizable: true,
        },
        minHeight: 180,
        formConfig: {
          // 全局禁用vxe-table的表单配置，使用formOptions
          enabled: false,
        },
        proxyConfig: {
          autoLoad: true,
          response: {
            result: 'items',
            total: 'total',
            list: 'items',
          },
          showActiveMsg: true,
          showResponseMsg: false,
        },
        round: true,
        showOverflow: true,
        size: 'small',
      } as VxeTableGridOptions,
    });

    // 表格配置项可以用 cellRender: { name: 'CellImage' },
    vxeUI.renderer.add('CellImage', {
      renderTableDefault(renderOpts, params) {
        const { props } = renderOpts;
        const { column, row } = params;
        return h(NImage, { src: row[column.field], ...props });
      },
    });

    // 表格配置项可以用 cellRender: { name: 'CellLink' },
    vxeUI.renderer.add('CellLink', {
      renderTableDefault(renderOpts) {
        const { props } = renderOpts;
        return h(
          NButton,
          { size: 'small', type: 'primary', quaternary: true },
          { default: () => props?.text },
        );
      },
    });

    vxeUI.renderer.add('CellTag', {
      renderTableDefault({ options, props }, { column, row }) {
        const value = row[column.field];
        const tagOptions = options ?? [
          { label: $t('common.enabled'), type: 'success', value: 1 },
          { label: $t('common.disabled'), type: 'error', value: 0 },
        ];
        const tagItem = tagOptions.find((item) => item.value === value);
        return h(
          NTag,
          {
            ...props,
            bordered: false,
            type: tagItem?.type,
          },
          { default: () => tagItem?.label ?? String(value ?? '') },
        );
      },
    });

    vxeUI.renderer.add('CellSwitch', {
      renderTableDefault({ attrs, props }, { column, row }) {
        const loadingKey = `__loading_${String(column.field)}`;
        const finallyProps = {
          ...props,
          checkedValue: 1,
          loading: row[loadingKey] ?? false,
          uncheckedValue: 0,
          value: row[column.field],
          'onUpdate:value': onChange,
        };

        async function onChange(newVal: any) {
          row[loadingKey] = true;
          try {
            const result = await attrs?.beforeChange?.(newVal, row);
            if (result !== false) {
              row[column.field] = newVal;
            }
          } finally {
            row[loadingKey] = false;
          }
        }

        return h(NSwitch, finallyProps);
      },
    });

    vxeUI.renderer.add('CellOperation', {
      renderTableDefault({ attrs, options, props }, { column, row }) {
        const defaultProps = {
          quaternary: true,
          size: 'small',
          type: 'primary',
          ...props,
        };

        let justifyContent = 'flex-end';
        if (column.align === 'center') {
          justifyContent = 'center';
        } else if (column.align === 'left') {
          justifyContent = 'flex-start';
        }

        const presets: Record<string, Record<string, any>> = {
          delete: {
            text: $t('common.delete'),
            type: 'error',
          },
          edit: {
            text: $t('common.edit'),
          },
        };

        const operations = (options || ['edit', 'delete'])
          .map((option) => {
            if (isString(option)) {
              return presets[option]
                ? { code: option, ...presets[option], ...defaultProps }
                : { code: option, text: option, ...defaultProps };
            }
            return { ...defaultProps, ...presets[option.code], ...option };
          })
          .map((option) => {
            const buttonProps: Record<string, any> = {};
            Object.keys(option).forEach((key) => {
              buttonProps[key] = isFunction(option[key]) ? option[key](row) : option[key];
            });
            return buttonProps;
          })
          .filter((option) => option.show !== false);

        function onClick(code: string) {
          attrs?.onClick?.({ code, row });
        }

        function renderButton(option: Record<string, any>, listen = true) {
          return h(
            NButton,
            {
              ...option,
              text: true,
              onClick: listen ? () => onClick(option.code) : undefined,
            },
            { default: () => option.text },
          );
        }

        function renderDelete(option: Record<string, any>) {
          return h(
            NPopconfirm,
            {
              negativeText: $t('common.cancel'),
              onPositiveClick: () => onClick(option.code),
              positiveText: $t('common.confirm'),
            },
            {
              default: () =>
                $t('ui.actionMessage.deleteConfirm', [
                  row[attrs?.nameField || 'name'],
                ]),
              trigger: () => renderButton(option, false),
            },
          );
        }

        return h(
          'div',
          {
            class: 'flex table-operations gap-1',
            style: { justifyContent },
          },
          operations.map((option) =>
            option.code === 'delete' ? renderDelete(option) : renderButton(option),
          ),
        );
      },
    });

    // 这里可以自行扩展 vxe-table 的全局配置，比如自定义格式化
    // vxeUI.formats.add
  },
  useVbenForm,
});

export const useVbenVxeGrid = <T extends Record<string, any>>(
  ...rest: Parameters<typeof useGrid<T, ComponentType, ComponentPropsMap>>
) => useGrid<T, ComponentType, ComponentPropsMap>(...rest);

export type OnActionClickParams<T = Record<string, any>> = {
  code: string;
  row: T;
};

export type OnActionClickFn<T = Record<string, any>> = (
  params: OnActionClickParams<T>,
) => void;

export type * from '@vben/plugins/vxe-table';

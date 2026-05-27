import type { Recordable } from '@vben/types';

import { requestClient } from '#/api/request';

export namespace SystemUserApi {
  export interface SystemUser {
    createTime: string;
    id: string;
    realName: string;
    remark: string;
    role: 'admin' | 'super' | 'user';
    status: 0 | 1;
    username: string;
  }

  export interface UserPayload {
    realName: string;
    remark?: string;
    role: 'admin' | 'super' | 'user';
    status: 0 | 1;
    username: string;
  }
}

export async function getUserList(params: Recordable<any>) {
  return requestClient.get<{
    items: SystemUserApi.SystemUser[];
    total: number;
  }>('/system/user/list', {
    params,
  });
}

export async function createUser(data: SystemUserApi.UserPayload) {
  return requestClient.post<SystemUserApi.SystemUser>('/system/user', data);
}

export async function updateUser(
  id: string,
  data: Partial<SystemUserApi.UserPayload>,
) {
  return requestClient.put<SystemUserApi.SystemUser>(`/system/user/${id}`, data);
}

export async function deleteUser(id: string) {
  return requestClient.delete<SystemUserApi.SystemUser>(`/system/user/${id}`);
}
